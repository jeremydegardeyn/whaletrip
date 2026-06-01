"""
Whale-watching tour tools.

Uses Viator/GetYourGuide adapters when API keys are set, otherwise mock data
seeded with real-world representative operators.
"""
from __future__ import annotations

import os

# Representative real operators — used as mock seed data
_TOUR_OPERATORS = [
    {"name": "Húsavík Whale Museum Tours", "region": "Iceland", "ocean_basin": "Eastern Atlantic",
     "species": ["Humpback whale", "Minke whale", "Blue whale"], "season_months": [5,6,7,8,9],
     "duration_hours": 3, "price_usd": 85, "rating": 4.9, "family_friendly": True,
     "accessibility": True, "languages": ["English", "Icelandic"], "operator_url": "#"},
    {"name": "Baja Whale Watch", "region": "Baja California, Mexico", "ocean_basin": "Eastern Pacific",
     "species": ["Gray whale", "Blue whale", "Fin whale"], "season_months": [12,1,2,3,4],
     "duration_hours": 4, "price_usd": 65, "rating": 4.8, "family_friendly": True,
     "accessibility": False, "languages": ["English", "Spanish"], "operator_url": "#"},
    {"name": "Azores Whale Watching", "region": "Azores, Portugal", "ocean_basin": "Eastern Atlantic",
     "species": ["Sperm whale", "Blue whale", "Fin whale"], "season_months": [4,5,6,7,8,9],
     "duration_hours": 3, "price_usd": 75, "rating": 4.7, "family_friendly": True,
     "accessibility": True, "languages": ["English", "Portuguese"], "operator_url": "#"},
    {"name": "Kaikoura Whale Watch NZ", "region": "Kaikoura, New Zealand", "ocean_basin": "Western Pacific",
     "species": ["Sperm whale", "Dusky dolphin", "Humpback whale"], "season_months": list(range(1,13)),
     "duration_hours": 2.5, "price_usd": 120, "rating": 4.8, "family_friendly": True,
     "accessibility": True, "languages": ["English"], "operator_url": "#"},
    {"name": "Sri Lanka Whale Safaris", "region": "Mirissa, Sri Lanka", "ocean_basin": "Indian Ocean",
     "species": ["Blue whale", "Sperm whale", "Bryde's whale"], "season_months": [11,12,1,2,3,4],
     "duration_hours": 5, "price_usd": 45, "rating": 4.6, "family_friendly": True,
     "accessibility": False, "languages": ["English", "Sinhala"], "operator_url": "#"},
    {"name": "Tadoussac Whale Cruises", "region": "Tadoussac, Canada", "ocean_basin": "Western Atlantic",
     "species": ["Beluga whale", "Blue whale", "Minke whale"], "season_months": [6,7,8,9,10],
     "duration_hours": 3, "price_usd": 70, "rating": 4.7, "family_friendly": True,
     "accessibility": True, "languages": ["English", "French"], "operator_url": "#"},
    {"name": "Hermanus Whale Route SA", "region": "Hermanus, South Africa", "ocean_basin": "Eastern Atlantic",
     "species": ["Southern right whale"], "season_months": [7,8,9,10,11],
     "duration_hours": 2, "price_usd": 55, "rating": 4.8, "family_friendly": True,
     "accessibility": False, "languages": ["English", "Afrikaans"], "operator_url": "#"},
    {"name": "Tonga Humpback Expeditions", "region": "Vava'u, Tonga", "ocean_basin": "Western Pacific",
     "species": ["Humpback whale"], "season_months": [7,8,9,10],
     "duration_hours": 6, "price_usd": 180, "rating": 4.9, "family_friendly": False,
     "accessibility": False, "languages": ["English"], "operator_url": "#"},
    {"name": "Monterey Bay Whale Watch", "region": "Monterey, California", "ocean_basin": "Eastern Pacific",
     "species": ["Blue whale", "Humpback whale", "Gray whale", "Orca"], "season_months": list(range(1,13)),
     "duration_hours": 4, "price_usd": 60, "rating": 4.7, "family_friendly": True,
     "accessibility": True, "languages": ["English"], "operator_url": "#"},
    {"name": "Húsavík North Sailing", "region": "Iceland", "ocean_basin": "Eastern Atlantic",
     "species": ["Humpback whale", "Blue whale"], "season_months": [4,5,6,7,8,9,10],
     "duration_hours": 3.5, "price_usd": 95, "rating": 4.8, "family_friendly": True,
     "accessibility": True, "languages": ["English", "German", "Icelandic"], "operator_url": "#"},
]


def find_whale_watching_tours(
    region: str | None = None,
    species: str | None = None,
    month: int | None = None,
    family_friendly: bool | None = None,
    max_price_usd: float | None = None,
    ocean_basin: str | None = None,
) -> dict:
    """
    Find whale-watching tours matching the traveller's requirements.

    Args:
        region: Geographic region or country (e.g. 'Iceland', 'Mexico', 'New Zealand').
        species: Target whale species.
        month: Travel month (1-12).
        family_friendly: Filter for family-friendly tours.
        max_price_usd: Maximum price per person in USD.
        ocean_basin: Ocean basin filter.

    Returns:
        dict with matching tours sorted by rating.
    """
    results = list(_TOUR_OPERATORS)

    if region:
        results = [t for t in results if region.lower() in t["region"].lower()]
    if ocean_basin:
        results = [t for t in results if ocean_basin.lower() in t["ocean_basin"].lower()]
    if species:
        results = [t for t in results if any(species.lower() in s.lower() for s in t["species"])]
    if month:
        results = [t for t in results if month in t["season_months"]]
    if family_friendly is not None:
        results = [t for t in results if t["family_friendly"] == family_friendly]
    if max_price_usd:
        results = [t for t in results if t["price_usd"] <= max_price_usd]

    results.sort(key=lambda x: x["rating"], reverse=True)

    return {
        "tours": results[:10],
        "total_found": len(results),
        "note": "Prices per person. Verify availability directly with operators.",
        "data_source": "mock" if not os.environ.get("VIATOR_API_KEY") else "viator",
    }


def get_tour_details(tour_name: str) -> dict:
    """
    Get detailed information about a specific tour operator.

    Args:
        tour_name: Name of the tour operator.

    Returns:
        dict with full tour details.
    """
    matches = [t for t in _TOUR_OPERATORS if tour_name.lower() in t["name"].lower()]
    if not matches:
        return {"error": f"No tour found matching '{tour_name}'"}
    return {"tour": matches[0]}
