
from datetime import datetime, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from .config import get_settings


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes used by Open-Meteo.
WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}

# Codes where being outside is a poor idea.
_BAD_OUTDOOR_CODES = {
    55, 56, 57, 65, 66, 67, 75, 77, 82, 85, 86, 95, 96, 99,
}
_WET_CODES = {
    51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
    71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99,
}


def _distance_m(
    lat1: float, lon1: float, lat2: float | None, lon2: float | None
) -> int | None:
    """Straight-line distance in metres (haversine)."""
    if lat2 is None or lon2 is None:
        return None

    from math import asin, cos, radians, sin, sqrt

    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return int(2 * 6371000 * asin(sqrt(a)))


def summarize_weather(
    current: dict[str, Any],
    today: dict[str, Any],
) -> dict[str, Any]:
    """Turn raw Open-Meteo numbers into facts the agent can reason about."""

    code = current.get("weather_code")
    description = WEATHER_CODES.get(code, "unknown conditions")

    temperature = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    wind = current.get("wind_speed_10m") or 0
    precipitation = current.get("precipitation") or 0

    probabilities = today.get("precipitation_probability_max") or [None]
    rain_chance = probabilities[0]

    is_wet = code in _WET_CODES or precipitation > 0.2
    outdoor_ok = not (
        code in _BAD_OUTDOOR_CODES
        or wind >= 45
        or (feels_like is not None and (feels_like <= -5 or feels_like >= 40))
    )

    parts = [description]
    if temperature is not None:
        parts.append(f"{round(temperature)}°C")
    if feels_like is not None and temperature is not None and abs(feels_like - temperature) >= 3:
        parts.append(f"feels like {round(feels_like)}°C")
    if rain_chance is not None:
        parts.append(f"{rain_chance}% chance of rain today")

    return {
        "summary": ", ".join(parts),
        "description": description,
        "is_wet": bool(is_wet),
        "outdoor_ok": bool(outdoor_ok),
        "rain_chance_today": rain_chance,
    }


def get_current_context(
    timezone_name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    city: str | None = None,
) -> dict[str, Any]:
    """Local time, part of day and what location information is available.

    The browser sends its IANA timezone; the server clock is only a fallback.
    """

    tz_used = "UTC"
    now = datetime.now(dt_timezone.utc)

    if timezone_name:
        try:
            now = datetime.now(ZoneInfo(timezone_name))
            tz_used = timezone_name
        except (ZoneInfoNotFoundError, ValueError):
            pass

    hour = now.hour

    if 5 <= hour < 12:
        part_of_day = "morning"
    elif 12 <= hour < 17:
        part_of_day = "afternoon"
    elif 17 <= hour < 21:
        part_of_day = "evening"
    else:
        part_of_day = "night"

    return {
        "local_time": now.strftime("%H:%M"),
        "local_date": now.strftime("%Y-%m-%d"),
        "weekday": now.strftime("%A"),
        "part_of_day": part_of_day,
        "is_daylight_likely": 6 <= hour < 19,
        "timezone": tz_used,
        "location_shared": latitude is not None and longitude is not None,
        "city": city,
    }


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

        current = data.get("current", {})
        today = data.get("daily", {})

        return {
            "ok": True,
            "provider": "Open-Meteo",
            "location": resolved_name,
            "country": country,
            "current": current,
            "today": today,
            "timezone": data.get("timezone"),
            **summarize_weather(current, today),
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

    settings = get_settings()
    elements: list[dict[str, Any]] = []
    last_error = None

    # The public Overpass servers are busy and rate-limit often,
    # so try each configured mirror before giving up.
    with httpx.Client(
        timeout=20.0,
        headers={"User-Agent": settings.http_user_agent},
    ) as client:
        for overpass_url in settings.overpass_urls:
            try:
                response = client.post(
                    overpass_url,
                    data={"data": query},
                )
                response.raise_for_status()
                elements = response.json().get("elements", [])
                last_error = None
                break
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc

    if last_error is not None:
        return {
            "ok": False,
            "error": "The nearby-place service is temporarily unavailable.",
        }

    try:

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
                "distance_m": _distance_m(
                    float(latitude), float(longitude), lat, lon
                ),
                "website": tags.get("website"),
                "opening_hours": tags.get("opening_hours"),
                "source": "OpenStreetMap",
            })

        places.sort(
            key=lambda place: (
                place["distance_m"] is None,
                place["distance_m"] or 0,
            )
        )

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