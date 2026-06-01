from __future__ import annotations

import structlog
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter, ArrayQueryParameter

from app.config import get_settings
from app.models.whale import (
    SightingsFilter,
    WhaleSighting,
    HeatmapCell,
    SpeciesSummary,
)

logger = structlog.get_logger()
settings = get_settings()


def _get_client() -> bigquery.Client:
    return bigquery.Client(project=settings.gcp_project_id)


def get_sightings(f: SightingsFilter) -> tuple[list[WhaleSighting], int]:
    client = _get_client()

    conditions: list[str] = []
    params: list = []

    if f.species:
        conditions.append("LOWER(species) LIKE LOWER(@species_pattern)")
        params.append(ScalarQueryParameter("species_pattern", "STRING", f"%{f.species}%"))
    if f.month:
        conditions.append("month = @month")
        params.append(ScalarQueryParameter("month", "INT64", f.month))
    if f.ocean_basin:
        conditions.append("ocean_basin = @ocean_basin")
        params.append(ScalarQueryParameter("ocean_basin", "STRING", f.ocean_basin))
    if f.climate_zone:
        conditions.append("climate_zone = @climate_zone")
        params.append(ScalarQueryParameter("climate_zone", "STRING", f.climate_zone))
    if f.year_min:
        conditions.append("year >= @year_min")
        params.append(ScalarQueryParameter("year_min", "INT64", f.year_min))
    if f.year_max:
        conditions.append("year <= @year_max")
        params.append(ScalarQueryParameter("year_max", "INT64", f.year_max))
    if f.lat_min is not None:
        conditions.append("latitude >= @lat_min")
        params.append(ScalarQueryParameter("lat_min", "FLOAT64", f.lat_min))
    if f.lat_max is not None:
        conditions.append("latitude <= @lat_max")
        params.append(ScalarQueryParameter("lat_max", "FLOAT64", f.lat_max))
    if f.lng_min is not None:
        conditions.append("longitude >= @lng_min")
        params.append(ScalarQueryParameter("lng_min", "FLOAT64", f.lng_min))
    if f.lng_max is not None:
        conditions.append("longitude <= @lng_max")
        params.append(ScalarQueryParameter("lng_max", "FLOAT64", f.lng_max))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
          sighting_id, species, genus, latitude, longitude,
          observation_date, year, month,
          country_code, region, observation_source,
          individual_count, ocean_basin, climate_zone, season
        FROM `{settings.bq_sightings_table}`
        {where}
        ORDER BY observation_date DESC
        LIMIT @limit
    """
    params.append(ScalarQueryParameter("limit", "INT64", f.limit))

    job_config = QueryJobConfig(query_parameters=params)
    rows = list(client.query(query, job_config=job_config).result())

    sightings = [WhaleSighting(**dict(row.items())) for row in rows]

    count_query = f"""
        SELECT COUNT(*) AS total
        FROM `{settings.bq_sightings_table}`
        {where}
    """
    count_params = [p for p in params if p.name != "limit"]
    count_job = QueryJobConfig(query_parameters=count_params)
    total = list(client.query(count_query, count_job).result())[0].total

    logger.info("sightings_query", count=len(sightings), total=total)
    return sightings, total


def get_heatmap(month: int | None, species: str | None) -> list[HeatmapCell]:
    client = _get_client()
    conditions = []
    params = []

    if month:
        conditions.append("month = @month")
        params.append(ScalarQueryParameter("month", "INT64", month))
    if species:
        conditions.append("LOWER(species) LIKE LOWER(@species)")
        params.append(ScalarQueryParameter("species", "STRING", f"%{species}%"))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
          lat_grid, lng_grid, month, species,
          ocean_basin, sighting_count, individual_count,
          centroid_lat, centroid_lng
        FROM `{settings.bq_heatmap_table}`
        {where}
        ORDER BY sighting_count DESC
        LIMIT 100000
    """
    job_config = QueryJobConfig(query_parameters=params)
    rows = list(client.query(query, job_config=job_config).result())
    return [HeatmapCell(**dict(row.items())) for row in rows]


def get_species_list() -> list[SpeciesSummary]:
    client = _get_client()
    query = f"""
        SELECT
          species, total_sightings, total_individuals,
          avg_latitude, avg_longitude,
          ocean_basins, active_months_count, countries_count
        FROM `{settings.bq_species_table}`
        ORDER BY total_sightings DESC
        LIMIT 200
    """
    rows = list(client.query(query).result())
    return [SpeciesSummary(**dict(row.items())) for row in rows]


def query_agent_context(
    species: str | None = None,
    month: int | None = None,
    ocean_basin: str | None = None,
) -> dict:
    """Compact summary payload for the Whale Intelligence Agent."""
    client = _get_client()
    params = []
    conditions = []

    if species:
        conditions.append("LOWER(species) LIKE LOWER(@species)")
        params.append(ScalarQueryParameter("species", "STRING", f"%{species}%"))
    if month:
        conditions.append("month = @month")
        params.append(ScalarQueryParameter("month", "INT64", month))
    if ocean_basin:
        conditions.append("ocean_basin = @ocean_basin")
        params.append(ScalarQueryParameter("ocean_basin", "STRING", ocean_basin))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
          species,
          ocean_basin,
          month,
          SUM(sighting_count)   AS sightings,
          SUM(individual_count) AS individuals,
          ROUND(AVG(centroid_lat), 2) AS avg_lat,
          ROUND(AVG(centroid_lng), 2) AS avg_lng
        FROM `{settings.bq_heatmap_table}`
        {where}
        GROUP BY species, ocean_basin, month
        ORDER BY sightings DESC
        LIMIT 50
    """
    job_config = QueryJobConfig(query_parameters=params)
    rows = list(client.query(query, job_config=job_config).result())
    return {
        "observations": [dict(r.items()) for r in rows],
        "species_queried": species,
        "month_queried": month,
        "ocean_basin_queried": ocean_basin,
    }
