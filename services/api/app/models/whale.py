from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class WhaleSighting(BaseModel):
    sighting_id: str
    species: str
    genus: Optional[str] = None
    latitude: float
    longitude: float
    observation_date: Optional[date] = None
    year: Optional[int] = None
    month: Optional[int] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    observation_source: Optional[str] = None
    individual_count: int = 1
    ocean_basin: Optional[str] = None
    climate_zone: Optional[str] = None
    season: Optional[str] = None


class HeatmapCell(BaseModel):
    lat_grid: float
    lng_grid: float
    month: int
    species: str
    ocean_basin: Optional[str] = None
    sighting_count: int
    individual_count: int
    centroid_lat: float
    centroid_lng: float


class SpeciesSummary(BaseModel):
    species: str
    total_sightings: int
    total_individuals: int
    avg_latitude: float
    avg_longitude: float
    ocean_basins: str
    active_months_count: int
    countries_count: int


class SightingsFilter(BaseModel):
    species: Optional[str] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    ocean_basin: Optional[str] = None
    climate_zone: Optional[str] = None
    year_min: Optional[int] = Field(None, ge=1900)
    year_max: Optional[int] = Field(None, le=2030)
    lat_min: Optional[float] = Field(None, ge=-90, le=90)
    lat_max: Optional[float] = Field(None, ge=-90, le=90)
    lng_min: Optional[float] = Field(None, ge=-180, le=180)
    lng_max: Optional[float] = Field(None, ge=-180, le=180)
    limit: int = Field(5000, ge=1, le=50000)


class SightingsResponse(BaseModel):
    sightings: list[WhaleSighting]
    total: int
    filters_applied: dict


class HeatmapResponse(BaseModel):
    cells: list[HeatmapCell]
    month: Optional[int]
    species: Optional[str]


class SpeciesListResponse(BaseModel):
    species: list[SpeciesSummary]
    total: int
