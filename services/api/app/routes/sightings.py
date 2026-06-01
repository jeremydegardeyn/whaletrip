from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.models.whale import SightingsFilter, SightingsResponse, HeatmapResponse, SpeciesListResponse
from app.services import bigquery_service

router = APIRouter(prefix="/sightings", tags=["sightings"])


@router.get("", response_model=SightingsResponse)
async def list_sightings(
    species: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    ocean_basin: Optional[str] = Query(None),
    climate_zone: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None, ge=1900),
    year_max: Optional[int] = Query(None, le=2030),
    lat_min: Optional[float] = Query(None, ge=-90, le=90),
    lat_max: Optional[float] = Query(None, ge=-90, le=90),
    lng_min: Optional[float] = Query(None, ge=-180, le=180),
    lng_max: Optional[float] = Query(None, ge=-180, le=180),
    limit: int = Query(5000, ge=1, le=50000),
):
    f = SightingsFilter(
        species=species, month=month, ocean_basin=ocean_basin,
        climate_zone=climate_zone, year_min=year_min, year_max=year_max,
        lat_min=lat_min, lat_max=lat_max, lng_min=lng_min, lng_max=lng_max,
        limit=limit,
    )
    sightings, total = bigquery_service.get_sightings(f)
    filters_applied = {k: v for k, v in f.model_dump().items() if v is not None and k != "limit"}
    return SightingsResponse(sightings=sightings, total=total, filters_applied=filters_applied)


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    month: Optional[int] = Query(None, ge=1, le=12),
    species: Optional[str] = Query(None),
):
    cells = bigquery_service.get_heatmap(month=month, species=species)
    return HeatmapResponse(cells=cells, month=month, species=species)


@router.get("/species", response_model=SpeciesListResponse)
async def list_species():
    species = bigquery_service.get_species_list()
    return SpeciesListResponse(species=species, total=len(species))


OCEAN_BASINS = [
    "Eastern Pacific", "Western Atlantic", "Eastern Atlantic",
    "Indian Ocean", "Western Pacific",
]

CLIMATE_ZONES = ["Arctic", "North Temperate", "Tropical", "South Temperate", "Antarctic"]

MONTHS = [
    {"value": 1, "label": "January"}, {"value": 2, "label": "February"},
    {"value": 3, "label": "March"},   {"value": 4, "label": "April"},
    {"value": 5, "label": "May"},     {"value": 6, "label": "June"},
    {"value": 7, "label": "July"},    {"value": 8, "label": "August"},
    {"value": 9, "label": "September"}, {"value": 10, "label": "October"},
    {"value": 11, "label": "November"}, {"value": 12, "label": "December"},
]


@router.get("/filters/options")
async def filter_options():
    return {
        "ocean_basins": OCEAN_BASINS,
        "climate_zones": CLIMATE_ZONES,
        "months": MONTHS,
    }
