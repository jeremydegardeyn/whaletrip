"""Integration tests for sightings routes using mocked BigQuery service."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import date

from main import app
from app.models.whale import WhaleSighting

client = TestClient(app)

SAMPLE_SIGHTING = WhaleSighting(
    sighting_id="123",
    species="Megaptera novaeangliae",
    latitude=64.12,
    longitude=-21.94,
    observation_date=date(2023, 7, 15),
    year=2023,
    month=7,
    country_code="IS",
    region="Iceland",
    observation_source="GBIF",
    individual_count=3,
    ocean_basin="Eastern Atlantic",
    climate_zone="North Temperate",
    season="Summer",
)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@patch("app.routes.sightings.bigquery_service.get_sightings")
def test_list_sightings_no_filter(mock_bq):
    mock_bq.return_value = ([SAMPLE_SIGHTING], 1)
    resp = client.get("/sightings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["sightings"][0]["species"] == "Megaptera novaeangliae"
    assert data["filters_applied"] == {}


@patch("app.routes.sightings.bigquery_service.get_sightings")
def test_list_sightings_with_species_filter(mock_bq):
    mock_bq.return_value = ([SAMPLE_SIGHTING], 1)
    resp = client.get("/sightings?species=humpback&month=7")
    assert resp.status_code == 200
    call_args = mock_bq.call_args[0][0]
    assert call_args.species == "humpback"
    assert call_args.month == 7


def test_list_sightings_invalid_month():
    resp = client.get("/sightings?month=13")
    assert resp.status_code == 422


def test_list_sightings_limit_enforced():
    resp = client.get("/sightings?limit=99999")
    assert resp.status_code == 422


@patch("app.routes.sightings.bigquery_service.get_heatmap")
def test_heatmap_endpoint(mock_bq):
    from app.models.whale import HeatmapCell
    cell = HeatmapCell(
        lat_grid=64.0, lng_grid=-22.0, month=7, species="Megaptera novaeangliae",
        sighting_count=42, individual_count=126, centroid_lat=64.12, centroid_lng=-21.94
    )
    mock_bq.return_value = [cell]
    resp = client.get("/sightings/heatmap?month=7")
    assert resp.status_code == 200
    assert resp.json()["month"] == 7
    assert len(resp.json()["cells"]) == 1


@patch("app.routes.sightings.bigquery_service.get_species_list")
def test_species_list(mock_bq):
    from app.models.whale import SpeciesSummary
    mock_bq.return_value = [
        SpeciesSummary(
            species="Megaptera novaeangliae",
            total_sightings=50000,
            total_individuals=150000,
            avg_latitude=25.0,
            avg_longitude=-40.0,
            ocean_basins="Eastern Atlantic, Western Atlantic",
            active_months_count=12,
            countries_count=45,
        )
    ]
    resp = client.get("/sightings/species")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_filter_options():
    resp = client.get("/sightings/filters/options")
    assert resp.status_code == 200
    data = resp.json()
    assert "ocean_basins" in data
    assert "months" in data
    assert len(data["months"]) == 12
