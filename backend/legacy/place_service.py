import httpx


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def search_nearby_places(
    query: str,
    latitude: float,
    longitude: float,
    limit: int = 5,
) -> list[dict]:

    params = {
        "q": query,
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "limit": limit,
        "addressdetails": 1,
        "accept-language": "en",
    }

    headers = {
        "User-Agent": "TouchGrass/0.1 (open-source activity agent)"
    }

    response = httpx.get(
        NOMINATIM_URL,
        params=params,
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    results = response.json()

    places = []

    for place in results:
        places.append(
            {
                "name": place.get("display_name", "").split(",")[0],
                "display_name": place.get("display_name"),
                "latitude": float(place["lat"]),
                "longitude": float(place["lon"]),
                "type": place.get("type"),
                "category": place.get("class"),
            }
        )

    return places