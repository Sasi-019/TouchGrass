from __future__ import annotations

import math
from typing import Any

import httpx


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


CATEGORY_TAGS = {
    "park": """
        nwr["leisure"="park"](around:{radius},{latitude},{longitude});
    """,
    "cafe": """
        nwr["amenity"="cafe"](around:{radius},{latitude},{longitude});
    """,
    "restaurant": """
        nwr["amenity"="restaurant"](around:{radius},{latitude},{longitude});
    """,
    "temple": """
        nwr["amenity"="place_of_worship"]["religion"="hindu"]
        (around:{radius},{latitude},{longitude});
    """,
    "nature": """
        nwr["leisure"="nature_reserve"]
        (around:{radius},{latitude},{longitude});
        nwr["natural"](around:{radius},{latitude},{longitude});
    """,
    "outdoor": """
        nwr["sport"](around:{radius},{latitude},{longitude});
        nwr["leisure"](around:{radius},{latitude},{longitude});
    """,
}


def calculate_distance(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """
    Calculate approximate distance between two coordinates.

    Returns distance in kilometres.
    """

    earth_radius_km = 6371.0

    lat1 = math.radians(latitude1)
    lat2 = math.radians(latitude2)

    delta_lat = math.radians(latitude2 - latitude1)
    delta_lon = math.radians(longitude2 - longitude1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius_km * c


def _extract_coordinates(element: dict[str, Any]) -> tuple[float | None, float | None]:
    """
    Extract latitude and longitude from an Overpass element.
    """

    if element.get("type") == "node":
        return element.get("lat"), element.get("lon")

    center = element.get("center", {})

    return (
        center.get("lat"),
        center.get("lon"),
    )


def _clean_name(tags: dict[str, Any]) -> str | None:
    """
    Get the most useful human-readable name.
    """

    return (
        tags.get("name")
        or tags.get("name:en")
        or tags.get("official_name")
    )


async def find_nearby_places(
    latitude: float,
    longitude: float,
    category: str = "park",
    radius: int = 5000,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Find nearby places using OpenStreetMap's Overpass API.

    Supported categories:
    - park
    - cafe
    - restaurant
    - temple
    - nature
    - outdoor
    """

    category = category.lower().strip()

    if category not in CATEGORY_TAGS:
        category = "park"

    radius = max(500, min(radius, 10000))
    limit = max(1, min(limit, 10))

    query = f"""
    [out:json][timeout:15];

    (
        {CATEGORY_TAGS[category].format(
            radius=radius,
            latitude=latitude,
            longitude=longitude,
        )}
    );

    out center tags;
    """

    headers = {
        "User-Agent": "TouchGrass/1.0 (open-source activity agent)",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                OVERPASS_URL,
                data=query,
                headers=headers,
            )

            response.raise_for_status()

            data = response.json()

    except httpx.HTTPError:
        return []

    results: list[dict[str, Any]] = []

    for element in data.get("elements", []):
        tags = element.get("tags", {})

        name = _clean_name(tags)

        if not name:
            continue

        place_latitude, place_longitude = _extract_coordinates(element)

        if place_latitude is None or place_longitude is None:
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            place_latitude,
            place_longitude,
        )

        address_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city"),
        ]

        address = ", ".join(
            part for part in address_parts if part
        )

        results.append(
            {
                "name": name,
                "category": category,
                "latitude": place_latitude,
                "longitude": place_longitude,
                "distance_km": round(distance, 2),
                "address": address or None,
                "website": tags.get("website"),
                "phone": tags.get("phone"),
                "opening_hours": tags.get("opening_hours"),
            }
        )

    results.sort(
        key=lambda place: place["distance_km"]
    )

    return results[:limit]