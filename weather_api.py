import requests  # Open-Meteo and geocoding HTTP client.
from datetime import datetime, date  # Parsing helpers and "today" reference.


def city_name_from_timezone(tz_name: str) -> str:
    """Return the city component of a Continent/City timezone."""
    parts = tz_name.split("/")  # Break "Area/City" into its components.
    if len(parts) < 2:
        raise ValueError("Timezone does not contain a city part (use Continent/City timezones).")
    return parts[-1].replace("_", " ")  # Use the trailing segment and make it human readable.


def get_location_from_timezone(tz_name: str):
    """Geocode the timezone-derived city and return lat/lon plus display info."""
    city = city_name_from_timezone(tz_name)  # Derive the lookup keyword from the timezone string.
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1}  # Ask for the best match only.
    try:
        resp = requests.get(url, params=params, timeout=10)  # Call Open-Meteo's geocoder.
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while geocoding: {e}")
    data = resp.json()
    if "results" not in data or not data["results"]:
        raise ValueError(f"Could not find location for city derived from timezone: {tz_name}")
    r = data["results"][0]  # Take the top hit returned by the service.
    return (
        r["latitude"],  # Latitude that drives weather queries.
        r["longitude"],  # Longitude that drives weather queries.
        r.get("name", city),  # Display name for UI output (fallback to derived city).
        r.get("country_code", "")  # ISO country code if provided.
    )


def get_weather_for_datetime(dt_str: str, tz_name: str):
    """Fetch hourly weather for `dt_str` in `tz_name`, picking archive vs forecast automatically."""
    dt_requested = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)  # Align to whole hour.
    lat, lon, city_name, country_code = get_location_from_timezone(tz_name)  # Coordinates + metadata for API calls.

    date_str = dt_requested.strftime("%Y-%m-%d")  # Common date string for both APIs.
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        if dt_requested.date() < date.today()
        else "https://api.open-meteo.com/v1/forecast"
    )  # Choose the endpoint based on whether the datetime is past or present/future.

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",  # Only fetch the fields we display.
        "timezone": tz_name,
        "start_date": date_str,
        "end_date": date_str,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)  # Execute the actual weather call.
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while fetching weather: {e}")

    data = resp.json()
    hourly = data.get("hourly", {})  # Parallel arrays keyed by measurement type.
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    hums = hourly.get("relative_humidity_2m", [])
    precs = hourly.get("precipitation", [])

    if not times:
        raise ValueError("No hourly weather data returned for that date (out of range?).")

    index = None
    for i, t in enumerate(times):
        if datetime.fromisoformat(t) == dt_requested:  # Find exact hour match (minutes already zeroed).
            index = i
            break

    if index is None:
        raise ValueError("No weather exactly at that hour (set minutes to 00).")

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
