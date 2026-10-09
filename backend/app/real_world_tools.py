
from typing import Any

import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def geocode_city(location: str) -> dict[str, Any] | None:
    """Convert a city or place name to coordinates."""
    with httpx.Client(timeout=12.0) as client:
        response = client.get(
            GEOCODING_URL,
            params={
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            },
        )
        response.raise_for_status()
        results = response.json().get("results", [])

    if not results:
        return None

    place = results[0]
    return {
        "name": place.get("name", location),
        "country": place.get("country", ""),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "timezone": place.get("timezone", "auto"),
    }


def get_weather(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """Retrieve live weather data for a city or coordinates."""
    if latitude is None or longitude is None:
        if not location:
            return {
                "ok": False,
                "error": "A city or coordinates are required for weather.",
            }

        try:
            place = geocode_city(location)
        except (httpx.HTTPError, ValueError):
            return {
                "ok": False,
                "error": "The location lookup service is unavailable.",
            }

        if not place:
            return {
                "ok": False,
                "error": f"Could not locate {location}.",
            }

        latitude = place["latitude"]
        longitude = place["longitude"]
        resolved_name = place["name"]
        timezone = place["timezone"]
        country = place["country"]
    else:
        resolved_name = location or "Your current location"
        timezone = "auto"
        country = ""

    try:
        with httpx.Client(timeout=12.0) as client:
            response = client.get(
                WEATHER_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,apparent_temperature,"
                        "relative_humidity_2m,precipitation,"
                        "weather_code,wind_speed_10m"
                    ),
                    "daily": (
                        "temperature_2m_max,temperature_2m_min,"
                        "precipitation_probability_max"
                    ),
                    "forecast_days": 1,
                    "timezone": timezone,
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "ok": True,
            "provider": "Open-Meteo",
            "location": resolved_name,
            "country": country,
            "current": data.get("current", {}),
            "today": data.get("daily", {}),
            "timezone": data.get("timezone"),
        }

    except (httpx.HTTPError, ValueError):
        return {
            "ok": False,
            "error": "The weather service is temporarily unavailable.",
        }


def search_nearby_places(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: int = 5000,
    category: str = "all",
) -> dict[str, Any]:
    """Find named real-world places using OpenStreetMap/Overpass."""
    if latitude is None or longitude is None:
        if not location:
            return {
                "ok": False,
                "error": "A city or coordinates are required to find places.",
            }

        try:
            place = geocode_city(location)
        except (httpx.HTTPError, ValueError):
            return {
                "ok": False,
                "error": "The location lookup service is unavailable.",
            }

        if not place:
            return {
                "ok": False,
                "error": f"Could not locate {location}.",
            }

        latitude = place["latitude"]
        longitude = place["longitude"]
        resolved_name = place["name"]
        country = place["country"]
    else:
        resolved_name = location or "Your current location"
        country = ""

    radius_m = max(500, min(int(radius_m), 10000))

    category_filters = {
        "parks": '["leisure"="park"]',
        "cafes": '["amenity"="cafe"]',
        "museums": '["tourism"="museum"]',
        "attractions": '["tourism"~"attraction|viewpoint|museum"]',
        "all": (
            '["leisure"="park"],'
            '["amenity"~"cafe|restaurant"],'
            '["tourism"~"attraction|museum|viewpoint"]'
        ),
    }

    filters = category_filters.get(category, category_filters["all"])

    # Each filter is a separate Overpass selector.
    selectors = []
    for item in filters.split(","):
        item = item.strip()
        if not item:
            continue
        selectors.append(
            f"node(around:{radius_m},{latitude},{longitude}){item};"
            f"way(around:{radius_m},{latitude},{longitude}){item};"
            f"relation(around:{radius_m},{latitude},{longitude}){item};"
        )

    query = "[out:json][timeout:15];(" + "".join(selectors) + ");out center tags 30;"

    try:
        with httpx.Client(
            timeout=20.0,
            headers={"User-Agent": "TouchGrass/1.0 (real-world activity assistant)"},
        ) as client:
            response = client.post(
                OVERPASS_URL,
                data={"data": query},
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])

        places = []
        seen = set()

        for item in elements:
            tags = item.get("tags", {})
            name = tags.get("name")
            if not name or name.casefold() in seen:
                continue

            seen.add(name.casefold())
            center = item.get("center", {})
            lat = item.get("lat", center.get("lat"))
            lon = item.get("lon", center.get("lon"))

            if tags.get("leisure") == "park":
                kind = "park"
            elif tags.get("amenity") == "cafe":
                kind = "cafe"
            elif tags.get("amenity") == "restaurant":
                kind = "restaurant"
            elif tags.get("tourism") == "museum":
                kind = "museum"
            else:
                kind = tags.get("tourism", "place")

            places.append({
                "name": name,
                "type": kind,
                "latitude": lat,
                "longitude": lon,
                "address": tags.get("addr:full") or ", ".join(
                    value for value in [
                        tags.get("addr:street"),
                        tags.get("addr:city"),
                    ] if value
                ),
                "website": tags.get("website"),
                "opening_hours": tags.get("opening_hours"),
                "source": "OpenStreetMap",
            })

        return {
            "ok": True,
            "provider": "OpenStreetMap/Overpass",
            "search_area": resolved_name,
            "radius_m": radius_m,
            "places": places[:15],
            "note": (
                "Opening hours may be missing or outdated. "
                "Do not claim a place is open unless verified."
            ),
        }

    except (httpx.HTTPError, ValueError):
        return {
            "ok": False,
            "error": "The nearby-place service is temporarily unavailable.",
        }