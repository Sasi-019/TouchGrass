import httpx


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


def get_weather(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "hourly": (
            "precipitation_probability,"
            "temperature_2m,"
            "weather_code"
        ),
        "forecast_days": 1,
        "timezone": "auto",
    }

    response = httpx.get(
        WEATHER_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    current = data.get("current", {})

    weather_code = current.get("weather_code")

    return {
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "precipitation": current.get("precipitation"),
        "weather": WEATHER_CODES.get(
            weather_code,
            "unknown",
        ),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "timezone": data.get("timezone"),
    }