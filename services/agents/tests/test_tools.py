"""Unit tests for agent tools (no BigQuery calls — tests mock layer)."""
import pytest
from unittest.mock import patch, MagicMock

from agents.tools.travel_tools import search_flights, search_hotels, estimate_trip_budget
from agents.tools.tour_tools import find_whale_watching_tours, get_tour_details
from agents.tools.destination_tools import get_destination_info, compare_destinations


# ── Travel tools ──────────────────────────────────────────────────────────────

def test_search_flights_returns_options():
    result = search_flights("Toronto", "Iceland", "June", 7)
    assert "flights" in result
    assert len(result["flights"]) > 0
    assert "cheapest_usd" in result
    assert result["flights"][0]["origin"] == "Toronto"


def test_search_flights_budget_filter():
    result = search_flights("Toronto", "Iceland", "June", 7, budget_usd=500)
    for f in result["flights"]:
        assert f["price_usd"] <= 500


def test_search_hotels_returns_options():
    result = search_hotels("Húsavík", "June", nights=5, guests=2)
    assert "hotels" in result
    assert len(result["hotels"]) > 0
    for h in result["hotels"]:
        assert "total_cost_usd" in h
        assert h["total_cost_usd"] == h["price_per_night_usd"] * 5


def test_estimate_budget_structure():
    result = estimate_trip_budget("Toronto", "Iceland", nights=7, guests=2)
    assert "total_usd" in result
    assert "per_person_usd" in result
    assert "breakdown_usd" in result
    breakdown = result["breakdown_usd"]
    assert sum(breakdown.values()) == result["total_usd"]


# ── Tour tools ────────────────────────────────────────────────────────────────

def test_find_tours_no_filter():
    result = find_whale_watching_tours()
    assert "tours" in result
    assert result["total_found"] > 0


def test_find_tours_by_region():
    result = find_whale_watching_tours(region="Iceland")
    assert result["total_found"] > 0
    for t in result["tours"]:
        assert "Iceland" in t["region"]


def test_find_tours_by_month():
    result = find_whale_watching_tours(month=7)
    for t in result["tours"]:
        assert 7 in t["season_months"]


def test_find_tours_family_filter():
    result = find_whale_watching_tours(family_friendly=True)
    for t in result["tours"]:
        assert t["family_friendly"] is True


def test_get_tour_details_found():
    result = get_tour_details("Húsavík")
    assert "tour" in result
    assert "Iceland" in result["tour"]["region"]


def test_get_tour_details_not_found():
    result = get_tour_details("Nonexistent Operator XYZ")
    assert "error" in result


# ── Destination tools ─────────────────────────────────────────────────────────

def test_destination_info_iceland():
    result = get_destination_info("Iceland")
    assert result.get("found") is not False
    assert "activities" in result
    assert result["hiking"] is True


def test_destination_info_with_month():
    result = get_destination_info("Iceland", travel_month=7)
    assert result["whale_season_active"] is True

    result_off = get_destination_info("Iceland", travel_month=2)
    assert result_off["whale_season_active"] is False


def test_destination_info_unknown():
    result = get_destination_info("Atlantis")
    assert result["found"] is False


def test_destination_with_interests():
    result = get_destination_info("Iceland", interests=["hiking", "photography"])
    assert "interest_scores" in result
    assert result["interest_scores"]["hiking_suitability"] == 10


def test_compare_destinations():
    result = compare_destinations(["Iceland", "Azores"], month=7)
    assert result["destinations_compared"] >= 1
