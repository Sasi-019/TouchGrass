from datetime import datetime


from .weather_service import get_weather
from .place_service import search_nearby_places


def get_current_context(
    latitude: float | None = None,
    longitude: float | None = None,
    place_query: str | None = None,
) -> dict:

    now = datetime.now().astimezone()

    context = {
        "current_time": now.strftime("%Y-%m-%d %H:%M"),
        "day": now.strftime("%A"),
        "latitude": latitude,
        "longitude": longitude,
        "weather": None,
        "nearby_places": [],
    }

    if latitude is not None and longitude is not None:

        try:
            context["weather"] = get_weather(
                latitude,
                longitude,
            )
        except Exception as exc:
            context["weather"] = {
                "error": str(exc)
            }

        if place_query:

            try:
                context["nearby_places"] = search_nearby_places(
                    query=place_query,
                    latitude=latitude,
                    longitude=longitude,
                )
            except Exception as exc:
                context["nearby_places"] = [
                    {
                        "error": str(exc)
                    }
                ]

    return context