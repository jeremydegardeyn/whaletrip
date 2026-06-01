"""
Travel planning tools with adapter interfaces.

Real API keys are read from environment variables. When absent, mock implementations
are used automatically. Add real providers by implementing the adapter interface.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Protocol


# ── Adapter Interfaces ─────────────────────────────────────────────────────────

class FlightProvider(Protocol):
    def search_flights(
        self, origin: str, destination: str, departure_date: str, return_date: str | None
    ) -> list[dict]: ...


class HotelProvider(Protocol):
    def search_hotels(
        self, destination: str, check_in: str, check_out: str, guests: int
    ) -> list[dict]: ...


# ── Mock Implementations ───────────────────────────────────────────────────────

_AIRLINE_NAMES = ["Air Canada", "United", "British Airways", "Qantas", "Lufthansa", "WestJet"]
_HOTEL_NAMES   = ["Coastal Inn", "Harbour View Hotel", "Ocean Retreat", "Whale Watcher Lodge"]


class MockFlightProvider:
    def search_flights(self, origin, destination, departure_date, return_date=None):
        base = random.randint(300, 2000)
        return [
            {
                "provider": "mock",
                "airline": random.choice(_AIRLINE_NAMES),
                "origin": origin,
                "destination": destination,
                "departure": departure_date,
                "return": return_date,
                "price_usd": base + i * 80,
                "duration_hours": random.uniform(2, 18),
                "stops": i,
                "booking_url": "#",
            }
            for i in range(3)
        ]


class MockHotelProvider:
    def search_hotels(self, destination, check_in, check_out, guests):
        base = random.randint(80, 300)
        return [
            {
                "provider": "mock",
                "name": f"{random.choice(_HOTEL_NAMES)} {destination}",
                "destination": destination,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "price_per_night_usd": base + i * 40,
                "stars": 3 + (i % 3),
                "amenities": ["wifi", "breakfast"] if i % 2 == 0 else ["wifi"],
                "booking_url": "#",
            }
            for i in range(4)
        ]


def _get_flight_provider() -> FlightProvider:
    return MockFlightProvider()


def _get_hotel_provider() -> HotelProvider:
    return MockHotelProvider()


# ── ADK-compatible tool functions ──────────────────────────────────────────────

def search_flights(
    origin_city: str,
    destination_region: str,
    departure_month: str,
    trip_duration_days: int = 7,
    budget_usd: float = 0,
) -> dict:
    """
    Search for flights to a whale-watching destination.

    Args:
        origin_city: Departure city (e.g. 'Toronto', 'London').
        destination_region: Target whale-watching region (e.g. 'Iceland', 'Baja California').
        departure_month: Month of travel (e.g. 'June', 'September').
        trip_duration_days: Length of trip in days.
        budget_usd: Maximum flight budget in USD.

    Returns:
        dict with flight options and price range.
    """
    provider = _get_flight_provider()
    return_date = f"{departure_month} +{trip_duration_days} days"
    flights = provider.search_flights(origin_city, destination_region, departure_month, return_date)

    if budget_usd and budget_usd > 0:
        flights = [f for f in flights if f["price_usd"] <= budget_usd]

    return {
        "flights": flights,
        "cheapest_usd": min((f["price_usd"] for f in flights), default=None),
        "note": "Prices are estimates. Book directly with the airline for accuracy.",
    }


def search_hotels(
    destination: str,
    check_in_month: str,
    nights: int = 5,
    guests: int = 2,
    budget_per_night_usd: float = 0,
) -> dict:
    """
    Search for hotels near a whale-watching destination.

    Args:
        destination: City or region name.
        check_in_month: Month of stay.
        nights: Number of nights.
        guests: Number of guests.
        budget_per_night_usd: Maximum budget per night in USD.

    Returns:
        dict with hotel options and total cost estimates.
    """
    provider = _get_hotel_provider()
    hotels = provider.search_hotels(destination, check_in_month, f"+{nights} nights", guests)

    if budget_per_night_usd and budget_per_night_usd > 0:
        hotels = [h for h in hotels if h["price_per_night_usd"] <= budget_per_night_usd]

    for h in hotels:
        h["total_cost_usd"] = h["price_per_night_usd"] * nights

    return {
        "hotels": hotels,
        "cheapest_per_night_usd": min((h["price_per_night_usd"] for h in hotels), default=None),
    }


def estimate_trip_budget(
    origin_city: str,
    destination: str,
    nights: int,
    guests: int,
    include_tours: bool = True,
) -> dict:
    """
    Estimate total budget for a whale-watching trip.

    Args:
        origin_city: Where the traveller is flying from.
        destination: Whale-watching destination.
        nights: Number of nights.
        guests: Number of travellers.
        include_tours: Whether to include whale-watching tour costs.

    Returns:
        dict with itemised budget estimate in USD.
    """
    flights = search_flights(origin_city, destination, "TBD", nights)
    hotels  = search_hotels(destination, "TBD", nights, guests)

    flight_cost = (flights.get("cheapest_usd") or 800) * guests
    hotel_cost  = (hotels.get("cheapest_per_night_usd") or 120) * nights
    tour_cost   = (150 * guests * 2) if include_tours else 0
    meals_cost  = 50 * nights * guests
    misc_cost   = 100 * guests

    total = flight_cost + hotel_cost + tour_cost + meals_cost + misc_cost

    return {
        "origin": origin_city,
        "destination": destination,
        "guests": guests,
        "nights": nights,
        "breakdown_usd": {
            "flights": flight_cost,
            "hotels": hotel_cost,
            "tours": tour_cost,
            "meals": meals_cost,
            "misc": misc_cost,
        },
        "total_usd": total,
        "per_person_usd": round(total / guests, 2),
        "note": "Estimates only. Actual prices vary by season and availability.",
    }
