"""BigQuery tools exposed to the Whale Intelligence Agent."""
from __future__ import annotations

import os
import structlog
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter

logger = structlog.get_logger()

_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
_DATASET = os.environ.get("BQ_DATASET", "whaletrip")


def _client() -> bigquery.Client:
    return bigquery.Client(project=_PROJECT)


def query_whale_sightings(
    species: str = "",
    month: int = 0,
    ocean_basin: str = "",
    climate_zone: str = "",
    limit: int = 20,
) -> dict:
    """
    Query whale sighting data from BigQuery.

    Args:
        species: Whale species name or partial name (e.g. 'blue', 'humpback').
        month: Month number 1-12.
        ocean_basin: One of: Eastern Pacific, Western Atlantic, Eastern Atlantic,
                     Indian Ocean, Western Pacific.
        climate_zone: One of: Arctic, North Temperate, Tropical, South Temperate, Antarctic.
        limit: Maximum results to return (default 20).

    Returns:
        dict with 'sightings' list and 'summary' statistics.
    """
    conditions = []
    params = []

    if species:
        conditions.append("LOWER(species) LIKE LOWER(@species)")
        params.append(ScalarQueryParameter("species", "STRING", f"%{species}%"))
    if month and month > 0:
        conditions.append("month = @month")
        params.append(ScalarQueryParameter("month", "INT64", month))
    if ocean_basin:
        conditions.append("ocean_basin = @ocean_basin")
        params.append(ScalarQueryParameter("ocean_basin", "STRING", ocean_basin))
    if climate_zone:
        conditions.append("climate_zone = @climate_zone")
        params.append(ScalarQueryParameter("climate_zone", "STRING", climate_zone))

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(ScalarQueryParameter("limit", "INT64", min(limit, 50)))

    query = f"""
        SELECT
          species, ocean_basin, climate_zone, month, season,
          ROUND(AVG(latitude), 2)  AS avg_lat,
          ROUND(AVG(longitude), 2) AS avg_lng,
          COUNT(*) AS sightings,
          SUM(individual_count) AS individuals,
          STRING_AGG(DISTINCT region ORDER BY region LIMIT 5) AS regions
        FROM `{_PROJECT}.{_DATASET}.whale_sightings`
        {where}
        GROUP BY species, ocean_basin, climate_zone, month, season
        ORDER BY sightings DESC
        LIMIT @limit
    """

    try:
        client = _client()
        job_config = QueryJobConfig(query_parameters=params)
        rows = list(client.query(query, job_config=job_config).result())
        sightings = [dict(r.items()) for r in rows]
        logger.info("bq_tool_query", rows=len(sightings))
        return {"sightings": sightings, "count": len(sightings)}
    except Exception as e:
        logger.error("bq_tool_error", error=str(e))
        return {"error": str(e), "sightings": []}


def get_species_seasonal_pattern(species: str) -> dict:
    """
    Get the full seasonal migration pattern for a whale species.

    Args:
        species: Whale species name.

    Returns:
        dict with monthly breakdown across ocean basins.
    """
    params = [ScalarQueryParameter("species", "STRING", f"%{species}%")]
    query = f"""
        SELECT
          month,
          ocean_basin,
          SUM(sighting_count)    AS sightings,
          SUM(individual_count)  AS individuals,
          ROUND(AVG(centroid_lat), 2)  AS avg_lat,
          ROUND(AVG(centroid_lng), 2)  AS avg_lng
        FROM `{_PROJECT}.{_DATASET}.seasonal_heatmap`
        WHERE LOWER(species) LIKE LOWER(@species)
        GROUP BY month, ocean_basin
        ORDER BY month, sightings DESC
    """
    try:
        client = _client()
        job_config = QueryJobConfig(query_parameters=params)
        rows = list(client.query(query, job_config=job_config).result())
        data = [dict(r.items()) for r in rows]

        # Restructure into month -> basin map for easier reasoning
        by_month: dict[int, list] = {}
        for row in data:
            m = row["month"]
            by_month.setdefault(m, []).append(row)

        return {"species": species, "seasonal_pattern": by_month}
    except Exception as e:
        return {"error": str(e)}


def get_top_whale_destinations(
    month: int = 0,
    species: str = "",
    limit: int = 10,
) -> dict:
    """
    Get top whale-watching destinations ranked by observation count.

    Args:
        month: Filter by month (1-12).
        species: Filter by species.
        limit: Number of destinations to return.

    Returns:
        dict with ranked destination list.
    """
    conditions = []
    params = []

    if month and month > 0:
        conditions.append("month = @month")
        params.append(ScalarQueryParameter("month", "INT64", month))
    if species:
        conditions.append("LOWER(species) LIKE LOWER(@species)")
        params.append(ScalarQueryParameter("species", "STRING", f"%{species}%"))

    params.append(ScalarQueryParameter("limit", "INT64", min(limit, 20)))
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT
          ocean_basin,
          climate_zone,
          species,
          SUM(sighting_count)   AS total_sightings,
          SUM(individual_count) AS total_individuals,
          ROUND(AVG(centroid_lat), 2) AS lat,
          ROUND(AVG(centroid_lng), 2) AS lng
        FROM `{_PROJECT}.{_DATASET}.seasonal_heatmap`
        {where}
        GROUP BY ocean_basin, climate_zone, species
        ORDER BY total_sightings DESC
        LIMIT @limit
    """
    try:
        client = _client()
        job_config = QueryJobConfig(query_parameters=params)
        rows = list(client.query(query, job_config=job_config).result())
        return {"destinations": [dict(r.items()) for r in rows]}
    except Exception as e:
        return {"error": str(e), "destinations": []}
