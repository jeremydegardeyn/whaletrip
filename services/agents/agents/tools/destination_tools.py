"""Destination intelligence tools — attractions, activities, dining, suitability."""
from __future__ import annotations

_DESTINATIONS: dict[str, dict] = {
    "iceland": {
        "country": "Iceland",
        "best_whale_months": [5, 6, 7, 8, 9],
        "top_ports": ["Húsavík", "Dalvík", "Reykjavík"],
        "activities": ["Northern Lights viewing", "Glacier hiking", "Hot springs/geothermal pools",
                       "Puffin watching", "Landscape photography", "Waterfall tours"],
        "hiking": True,
        "photography": True,
        "family_score": 8,
        "adventure_score": 9,
        "romance_score": 9,
        "avg_temp_celsius": {"summer": 12, "spring": 5, "autumn": 6},
        "currency": "ISK",
        "avg_daily_budget_usd": {"budget": 120, "mid": 220, "luxury": 400},
        "nearest_airports": ["KEF (Keflavík)"],
        "cuisine": ["Lamb soup", "Skyr", "Seafood", "Hot dogs"],
        "notes": "Midnight sun in summer makes whale watching magical. Book well ahead."
    },
    "azores": {
        "country": "Portugal (Azores)",
        "best_whale_months": [4, 5, 6, 7, 8, 9],
        "top_ports": ["Pico", "Horta", "São Miguel"],
        "activities": ["Volcano hiking", "Diving/snorkeling", "Caldeira swimming",
                       "Bird watching", "Whale photography from vigia lookouts"],
        "hiking": True,
        "photography": True,
        "family_score": 8,
        "adventure_score": 8,
        "romance_score": 9,
        "avg_temp_celsius": {"summer": 24, "spring": 18, "autumn": 22},
        "currency": "EUR",
        "avg_daily_budget_usd": {"budget": 70, "mid": 130, "luxury": 250},
        "nearest_airports": ["PDL (Ponta Delgada)", "HOR (Horta)"],
        "cuisine": ["Caldo de carne", "Alcatra", "Fresh tuna", "Queijo do Pico"],
        "notes": "Year-round whale presence. Sperm whales resident all year."
    },
    "baja california": {
        "country": "Mexico",
        "best_whale_months": [12, 1, 2, 3, 4],
        "top_ports": ["Guerrero Negro", "San Ignacio Lagoon", "Loreto", "La Paz"],
        "activities": ["Gray whale lagoon tours", "Snorkeling with sea lions", "Desert hiking",
                       "Kayaking", "Stargazing", "Cave paintings tours"],
        "hiking": True,
        "photography": True,
        "family_score": 9,
        "adventure_score": 8,
        "romance_score": 7,
        "avg_temp_celsius": {"winter": 20, "spring": 24},
        "currency": "MXN",
        "avg_daily_budget_usd": {"budget": 50, "mid": 100, "luxury": 200},
        "nearest_airports": ["MZT (Mazatlán)", "LAP (La Paz)"],
        "cuisine": ["Fish tacos", "Lobster Puerto Nuevo", "Machaca"],
        "notes": "Gray whale calving lagoons are UNESCO protected. Friendly whales approach boats."
    },
    "kaikoura": {
        "country": "New Zealand",
        "best_whale_months": list(range(1, 13)),
        "top_ports": ["Kaikoura"],
        "activities": ["Dolphin swimming", "Albatross watching", "Coastal walking trail",
                       "Seal colony visits", "Kayaking", "Scenic railway"],
        "hiking": True,
        "photography": True,
        "family_score": 9,
        "adventure_score": 8,
        "romance_score": 8,
        "avg_temp_celsius": {"summer": 22, "winter": 12},
        "currency": "NZD",
        "avg_daily_budget_usd": {"budget": 80, "mid": 150, "luxury": 280},
        "nearest_airports": ["CHC (Christchurch)", "WLG (Wellington)"],
        "cuisine": ["Crayfish", "Green-lipped mussels", "Hāngī"],
        "notes": "Sperm whales resident year-round due to deep underwater canyon."
    },
    "tadoussac": {
        "country": "Canada",
        "best_whale_months": [6, 7, 8, 9, 10],
        "top_ports": ["Tadoussac", "Baie-Sainte-Catherine", "Les Bergeronnes"],
        "activities": ["Beluga whale kayaking", "Fjord hiking", "Dune Tadoussac",
                       "Marine mammal museum", "Fall foliage tours"],
        "hiking": True,
        "photography": True,
        "family_score": 9,
        "adventure_score": 7,
        "romance_score": 8,
        "avg_temp_celsius": {"summer": 21, "spring": 12, "autumn": 14},
        "currency": "CAD",
        "avg_daily_budget_usd": {"budget": 80, "mid": 150, "luxury": 280},
        "nearest_airports": ["YBG (Bagotville)", "YQB (Quebec City)"],
        "cuisine": ["Poutine", "Tourtière", "Lobster", "Smoked salmon"],
        "notes": "St. Lawrence river confluence creates exceptional feeding grounds."
    },
}


def get_destination_info(
    destination: str,
    interests: str = "",
    travel_month: int = 0,
) -> dict:
    """
    Get detailed destination information for whale-watching travel planning.

    Args:
        destination: Destination name (e.g. 'Iceland', 'Azores', 'Baja California').
        interests: List of interests (e.g. ['hiking', 'photography', 'family']).
        travel_month: Month of planned travel (1-12).

    Returns:
        dict with destination details, suitability scores, and recommendations.
    """
    key = destination.lower()
    match = None
    for k, v in _DESTINATIONS.items():
        if k in key or key in k:
            match = v
            break

    if not match:
        return {
            "destination": destination,
            "found": False,
            "message": f"Detailed info not available for {destination}. "
                       "I can still provide general whale-watching guidance.",
        }

    result = dict(match)
    result["destination"] = destination

    if travel_month and travel_month > 0:
        result["whale_season_active"] = travel_month in match["best_whale_months"]

    if interests:
        scores: dict[str, int] = {}
        for interest in interests.split(","):
            interest = interest.strip()
            if "hik" in interest.lower():
                scores["hiking_suitability"] = 10 if match["hiking"] else 3
            if "photo" in interest.lower():
                scores["photography_suitability"] = 10 if match["photography"] else 5
            if "famil" in interest.lower():
                scores["family_suitability"] = match["family_score"]
            if "adventur" in interest.lower():
                scores["adventure_suitability"] = match["adventure_score"]
        result["interest_scores"] = scores

    return result


def compare_destinations(
    destinations: str,
    month: int = 0,
    budget_usd: float = 0,
) -> dict:
    """
    Compare multiple whale-watching destinations.

    Args:
        destinations: List of destination names to compare.
        month: Travel month for seasonal suitability check.
        budget_usd: Daily budget in USD for filtering.

    Returns:
        dict with comparison table.
    """
    comparison = []
    for dest in destinations.split(","):
        dest = dest.strip()
        info = get_destination_info(dest, travel_month=month)
        if info.get("found") is not False:
            if budget_usd and budget_usd > 0:
                mid_budget = info.get("avg_daily_budget_usd", {}).get("mid", 999)
                info["within_budget"] = mid_budget <= budget_usd
            comparison.append(info)

    return {"comparison": comparison, "destinations_compared": len(comparison)}
