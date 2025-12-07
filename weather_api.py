import requests  # Open-Meteo and geocoding HTTP client.
from datetime import datetime, date  # Parsing helpers and "today" reference.


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


def get_weather_for_datetime(dt_str: str, tz_name: str):  # Main entry for hourly weather lookups.
    """Fetch hourly weather for `dt_str` in `tz_name`, picking archive vs forecast automatically."""

    dt_requested = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)  # Align to whole hour.

    lat, lon, city_name, country_code = get_location_from_timezone(tz_name)  # Coordinates + metadata for API calls.

    date_str = dt_requested.strftime("%Y-%m-%d")  # Common date string for both APIs.

    url = (
        "https://archive-api.open-meteo.com/v1/archive"  # Historical endpoint.
        if dt_requested.date() < date.today()  # Use archive for past dates.
        else "https://api.open-meteo.com/v1/forecast"  # Forecast endpoint for present/future.
    )  # Choose the endpoint based on whether the datetime is past or present/future.

    params = {
        "latitude": lat,  # Include latitude in query.
        "longitude": lon,  # Include longitude in query.
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",  # Only fetch the fields we display.
        "timezone": tz_name,  # Request timezone-adjusted timestamps.
        "start_date": date_str,  # Limit to the requested date.
        "end_date": date_str,  # Same date for both bounds.
    }

    try:  # Execute the weather call and ensure success.
        resp = requests.get(url, params=params, timeout=10)  # Execute the actual weather call.
        resp.raise_for_status()  # Surface HTTP failures.
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network/API error while fetching weather: {e}")

    data = resp.json()  # Parse the returned JSON content.

    hourly = data.get("hourly", {})  # Parallel arrays keyed by measurement type.
    times = hourly.get("time", [])  # ISO stamps for each hour.
    temps = hourly.get("temperature_2m", [])  # Temperature list aligned with times.
    hums = hourly.get("relative_humidity_2m", [])  # Humidity list aligned with times.
    precs = hourly.get("precipitation", [])  # Precip list aligned with times.

    if not times:  # No hourly results were returned.
        raise ValueError("No hourly weather data returned for that date (out of range?).")  # Notify caller.

    index = None  # Placeholder for the matching hour index.

    for i, t in enumerate(times):  # Scan each timestamp.
        if datetime.fromisoformat(t) == dt_requested:  # Find exact hour match (minutes already zeroed).
            index = i
            break

    if index is None:  # API did not include the exact hour requested.
        raise ValueError("No weather exactly at that hour (set minutes to 00).")  # Suggest corrective action.

    return {
        "city": city_name,  # Display city name.
        "country": country_code,  # Country code for context.
        "time": times[index],  # Timestamp at the matched hour.
        "temperature": temps[index],  # Temperature value.
        "humidity": hums[index],  # Humidity percentage.
        "precipitation": precs[index],  # Precipitation amount.
        "latitude": lat,  # Latitude echoed back for completeness.
        "longitude": lon,  # Longitude echoed back for completeness.
    }
