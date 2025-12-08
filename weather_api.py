"""Helper module that owns every network call for weather + basic condition tagging."""

import requests  # Open-Meteo and geocoding HTTP client.
from datetime import datetime, date  # Parsing helpers and "today" reference.


def classify_condition(weathercode, precip, cloudcover):
    """Collapse Open-Meteo numeric fields into readable tags the GUI can reason about."""

    # --- Storm / Thunderstorm ---
    # Open-Meteo: 95 = thunderstorm, 96–99 = thunderstorm with hail
    if weathercode in (95, 96, 97, 98, 99):
        return "storm"

    # --- Snow ---
    # 71–78 = all snow types, 85–86 = heavy snow showers
    if weathercode in (71, 73, 75, 77, 85, 86):
        return "snow"

    # --- Rain ---
    # Any precipitation > 0 or weather codes indicating rain/drizzle/showers
    if precip > 0.1 or weathercode in (
        51, 53, 55,  # drizzle
        56, 57,      # freezing drizzle
        61, 63, 65,  # rain
        66, 67,      # freezing rain
        80, 81, 82   # rain showers
    ):
        return "rain"

    # --- Cloudy ---
    # 1 = mainly clear, 2 = partly cloudy, 3 = overcast
    # 45, 48 = fog
    if weathercode in (1, 2, 3, 45, 48) or cloudcover >= 60:
        return "cloudy"

    # --- Default ---
    return "clear"

def city_name_from_timezone(tz_name): # Helper for extracting the city portion.
    """Return the city component of a Continent/City timezone."""

    parts = tz_name.split("/")  # Break "Area/City" into its components.
    if len(parts) < 2:  # Guard against tz identifiers without a city component.
        raise ValueError("Timezone does not contain a city part (use Continent/City timezones).")  # Signal unsupported format.
    return parts[-1].replace("_", " ")  # Use the trailing segment and make it human readable.


def get_location_from_timezone(tz_name):  # Resolve geocoding metadata for a timezone.
    """Geocode the timezone-derived city and return lat/lon plus display info."""

    city = city_name_from_timezone(tz_name)  # Derive the lookup keyword from the timezone string.

    url = "https://geocoding-api.open-meteo.com/v1/search"  # Base geocoding endpoint.

    params = {"name": city, "count": 1}  # Ask for the best match only.

    try:  # Attempt the HTTP request.
        resp = requests.get(url, params=params, timeout=10)  # Call Open-Meteo's geocoder.
        resp.raise_for_status()  # Raise if the response indicates failure.
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while geocoding: {e}")  # Repackage network issues.

    data = resp.json()  # Decode JSON body.

    if "results" not in data or not data["results"]:
        raise ValueError(f"Could not find location for city derived from timezone: {tz_name}")  # Fail if no hits.

    r = data["results"][0]  # Take the top hit returned by the service.

    return (
        r["latitude"],  # Latitude that drives weather queries.
        r["longitude"],  # Longitude that drives weather queries.
        r.get("name", city),  # Display name for UI output (fallback to derived city).
        r.get("country_code", "")  # ISO country code if provided.
    )


def get_weather_for_datetime(dt_str: str, tz_name: str):
    """Fetch the hourly weather slice that matches the provided datetime + timezone."""

    # Parse once and clamp minutes/seconds because Open-Meteo only exposes full hours.
    dt_requested = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)

    # Timezone → best-guess city → geocoded coordinates.
    lat, lon, city_name, country_code = get_location_from_timezone(tz_name)

    date_str = dt_requested.strftime("%Y-%m-%d")  # Common date string for both APIs.

    url = (
        "https://archive-api.open-meteo.com/v1/archive"  # Historical endpoint.
        if dt_requested.date() < date.today()  # Use archive for past dates.
        else "https://api.open-meteo.com/v1/forecast"  # Forecast endpoint for present/future.
    )  # Choose the endpoint based on whether the datetime is past or present/future.

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weathercode,cloudcover",
        "timezone": tz_name,
        "start_date": date_str,
        "end_date": date_str,
    }

    try:  # Execute the weather call and ensure success.
        resp = requests.get(url, params=params, timeout=10)  # Execute the actual weather call.
        resp.raise_for_status()  # Surface HTTP failures.
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while fetching weather: {e}")

    data = resp.json()  # Parse the returned JSON content.

    hourly = data.get("hourly", {})
    times  = hourly.get("time", [])
    temps  = hourly.get("temperature_2m", [])
    hums   = hourly.get("relative_humidity_2m", [])
    precs  = hourly.get("precipitation", [])
    codes  = hourly.get("weathercode", [])
    clouds = hourly.get("cloudcover", [])



    if not times:  # No hourly results were returned.
        raise ValueError("No hourly weather data returned for that date (out of range?).")  # Notify caller.

    index = None  # Placeholder for the matching hour index.

    for i, t in enumerate(times):  # Scan each timestamp.
        if datetime.fromisoformat(t) == dt_requested:  # Find exact hour match (minutes already zeroed).
            index = i
            break

    if index is None:  # API did not include the exact hour requested.
        raise ValueError("No weather exactly at that hour (set minutes to 00).")  # Suggest corrective action.
    condition = classify_condition(
        weathercode=codes[index],
        precip=precs[index],
        cloudcover=clouds[index],
    )

    return {
        "city": city_name,
        "country": country_code,
        "time": times[index],
        "temperature": temps[index],
        "humidity": hums[index],
        "precipitation": precs[index],
        "weathercode": codes[index],
        "cloudcover": clouds[index],
        "condition": condition,   # ← NEW: clear / cloudy / rain / snow / storm
        "latitude": lat,
        "longitude": lon,
    }
