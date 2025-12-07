import requests
from datetime import datetime

def city_name_from_timezone(tz_name: str) -> str:
    """
    'Asia/Kolkata' -> 'Kolkata'
    'America/New_York' -> 'New York'
    If timezone has no city-like part, we raise.
    """
    parts = tz_name.split("/")
    if len(parts) < 2:
        raise ValueError("Timezone does not contain a city part (use Continent/City timezones).")
    return parts[-1].replace("_", " ")


def get_location_from_timezone(tz_name: str):
    """
    Use timezone string to guess city name, then geocode it.
    Returns (lat, lon, city_display_name, country_code).
    """
    city = city_name_from_timezone(tz_name)
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while geocoding: {e}")
    data = resp.json()
    if "results" not in data or not data["results"]:
        raise ValueError(f"Could not find location for city derived from timezone: {tz_name}")
    r = data["results"][0]
    return (
        r["latitude"],
        r["longitude"],
        r.get("name", city),
        r.get("country_code", "")
    )
def get_weather_for_datetime(dt_str: str, tz_name: str):
    """
    Get hourly weather for a specific datetime (tz_name timezone).
    dt_str: 'YYYY-MM-DD HH:MM:SS'
    """
    dt_requested = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    # Round to hour
    dt_requested = dt_requested.replace(minute=0, second=0)

    lat, lon, city_name, country_code = get_location_from_timezone(tz_name)

    date_str = dt_requested.strftime("%Y-%m-%d")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",
        "timezone": tz_name,
        "start_date": date_str,
        "end_date": date_str,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while fetching weather: {e}")

    data = resp.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    hums = hourly.get("relative_humidity_2m", [])
    precs = hourly.get("precipitation", [])

    if not times:
        raise ValueError("No hourly weather data returned for that date.")

    index = None
    for i, t in enumerate(times):
        t_dt = datetime.fromisoformat(t)
        if t_dt == dt_requested:
            index = i
            break

    if index is None:
        raise ValueError("No weather exactly at that hour (try changing minutes to 00).")

    return {
        "city": city_name,
        "country": country_code,
        "time": times[index],
        "temperature": temps[index],
        "humidity": hums[index],
        "precipitation": precs[index],
        "latitude": lat,
        "longitude": lon,
    }

