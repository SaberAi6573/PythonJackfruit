# PythonJackfruit

PythonJackfruit is a wxPython desktop utility that combines three workflows in one place:
- Convert any timestamp between two IANA timezones with DST-aware accuracy.
- Fetch the hourly weather that corresponds to the destination timezone and time.
- Compare historical exchange rates derived from the countries that own the selected timezones.

The app is opinionated about input quality so that downstream weather and currency calls succeed with minimal retries. This document dives into the runtime architecture, data flow, and operational tips so contributors can extend the tool confidently.

## Architecture Overview

Component | Responsibility | Dependencies
--------- | -------------- | ------------
`Tzpy.py` | GUI bootstrap, event wiring, timezone conversion, theme switching, feature orchestration | `wxPython`, `pytz`, `tzlocal`, local modules
`weather_api.py` | Geocode city names (Open-Meteo) and fetch hourly weather data (forecast or archive) | `requests`
`currency.py` | Map timezones to ISO country codes, resolve main currencies, fetch Frankfurter FX rates | `requests`, `pytz`
`tz_aliases.txt` | Optional alias sheet that maps legacy tz IDs to canonical names | —

Data flows from the GUI to helper modules in this order:
1. User input (datetime + timezones) triggers conversion.
2. The conversion result updates the background theme based on time-of-day buckets.
3. Weather and currency buttons reuse the same inputs, enrich them with remote API data, and render formatted summaries.

## Requirements

- Python 3.10+
- `wxPython`, `pytz`, `tzlocal`, `requests`

Install dependencies once:

```powershell
pip install wxPython pytz tzlocal requests
```

## Running the App

1. Open PowerShell inside the project folder (`PythonJackfruit`).
2. Launch the desktop client:
   ```powershell
   python Tzpy.py
   ```
3. Provide the source datetime using `YYYY-MM-DD HH:MM:SS` (minutes must be `00` for weather).
4. Choose **From TZ** (source) and **To TZ** (destination) from the dropdown lists.
5. Click **Convert Time** to view the converted timestamp plus an ambient theme that mirrors the destination brightness.
6. Click **Get Weather** to fetch temperature, humidity, and precipitation for the derived destination city.
7. Click **Compare 1 Unit** to derive currencies from the two timezones and show the exchange rate for the provided date.

## Feature Deep Dive

### Time Conversion & Theming
- Uses `pytz` to localize naïve datetimes and convert them safely with DST awareness.
- Background colors shift automatically depending on the converted or input hour (pre-dawn, sunrise, noon, sunset, late night) to provide a quick visual cue.
- The **Current Local** button (`tzlocal.get_localzone_name`) pre-fills the current timestamp and timezone to reduce typing.

### Weather Lookup
- Destination timezone is mapped to a best-guess city name (`Asia/Tokyo` → `Tokyo`).
- The name is geocoded via Open-Meteo’s free geocoding API (single-result search for clarity).
- The hourly weather endpoint switches between forecast and archive services depending on whether the requested date is in the past.
- Only round-hour timestamps are supported; the UI enforces this by hint text and the backend validates again.

### Currency Comparison
- Each timezone is mapped to an ISO country code using `pytz.country_timezones` plus alias lookups from `tz_aliases.txt`.
- Country code → currency code is resolved via RestCountries; successful lookups are cached for the process lifetime.
- Frankfurter provides the FX rate (historical if a date is given, latest otherwise). The UI fixes the comparison at `1 unit` to keep output compact.

## Module Reference

- **`Tzpy.py`**
   - `time_zone_converter`: localizes a naïve datetime to the source timezone, shifts it to the target timezone, and returns a formatted string.
   - `back_fore_ground`, `time_background_converter_input`, `time_background_converter_output`: drive the ambient theme based on user-entered or converted times.
   - `on_convert`, `on_now`, `on_weather`, `on_currency_convert`: wxPython event handlers that orchestrate conversions and delegate to helper modules.
   - UI setup code initializes every widget explicitly, wires events, and enters the wx main loop.
- **`weather_api.py`**
   - `city_name_from_timezone`: converts `Continent/City` into a human-readable city string.
   - `get_location_from_timezone`: uses Open-Meteo geocoding to turn the city string into `(lat, lon, display_name, country_code)`.
   - `get_weather_for_datetime`: selects archive vs. forecast API, enforces on-the-hour timestamps, and returns a dictionary with temperature, humidity, and precipitation values.
- **`currency.py`**
   - `_load_aliases`: loads `tz_aliases.txt`, allowing legacy timezone identifiers to piggyback on canonical zones.
   - `get_currency_from_country`: hits RestCountries once per ISO code and caches the currency result in-memory.
   - `get_currency_from_timezone`: maps a timezone (canonical or alias) to the owning country before resolving its currency.
   - `convert_currency`: queries Frankfurter for historical or latest FX rates and returns both the converted amount and the rate date.
- **`tz_aliases.txt`**
   - Plain text mapping in `alias=canonical` format.
   - Lines beginning with `#` are comments; blank lines are ignored.
   - Extend this file whenever you need to support legacy timezone strings that are not part of `pytz` anymore.

## Extending the App

- **Adding more aliases**: edit `tz_aliases.txt` with `old_id=new_id` entries. The loader applies them automatically at startup.
- **Caching policy**: both the weather and currency modules hit public APIs; consider persisting results if you need offline functionality.
- **UI tweaks**: `Tzpy.py` drives layout in absolute coordinates. Switching to sizers will make resizing easier if you plan to expand the window.

## Troubleshooting & FAQ

- `ModuleNotFoundError`: verify that requirements are installed in the interpreter that runs `Tzpy.py`.
- Weather requests fail with "No weather exactly at that hour": make sure the input minutes and seconds are `00`. Open-Meteo only returns hourly slices.
- Currency error mentioning aliases: ensure both dropdowns point to canonical city-based timezones. Plain offsets like `UTC` lack country context.
- GUI freezes or closes immediately: check PowerShell output for stack traces (API timeouts will print there). Slow networks may require reattempting.

## Roadmap Ideas

- Persist the last-used selections to disk so sessions can resume quickly.
- Add multi-currency conversion or amount inputs for the FX feature.
- Support additional weather providers with richer condition metadata or icons.

Feel free to open issues or pull requests with enhancements, bug reports, or documentation fixes.
