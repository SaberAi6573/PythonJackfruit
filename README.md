# PythonJackfruit

> A friendly “three-in-one” desktop buddy I built in college to convert timezones, peek at the weather, and compare currencies without hopping between websites.

## Why This Exists

During group projects we kept dropping links in chat: one for time math, another for weather, and a third for exchange rates. PythonJackfruit glues those steps into a single wxPython window so it feels like a mini productivity dashboard. The app still uses real APIs under the hood, but the UI is opinionated enough that classmates can jump in without worrying about weird formats.

## Quick Start (Lab Manual Style)

1. Make sure Python 3.10+ is installed.
2. Install the dependencies once:
   ```powershell
   pip install wxPython pytz tzlocal requests
   ```
3. Run the GUI from the project root:
   ```powershell
   python Tzpy.py
   ```
4. Type a datetime in `YYYY-MM-DD HH:MM:SS` (minutes must be `00` so the weather API lines up with hourly data).
5. Pick the source and destination timezones, then click **Convert Time**.
6. Use **Get Weather** and **Compare 1 Unit** to reuse the same inputs for weather + currency breakdowns.

## Feature Tour

### Time Conversion + Ambient Theme
- `pytz` handles the DST math so the converted time is trustworthy.
- Time buckets (pre-dawn, sunrise, day, evening, night) control the illustration behind the widgets. Rain/snow/storm variants keep the vibe accurate without hiding the controls.
- **Current Local** grabs the OS timezone via `tzlocal` and pre-fills the datetime so you can convert instantly.

### Weather Snapshot
- The destination timezone is translated into a city string (`Europe/Berlin` ➜ `Berlin`).
- Open-Meteo’s geocoder turns that string into latitude/longitude. With that info we call their hourly endpoint (forecast or archive, depending on whether the requested date is in the past).
- Returned data includes `temperature`, `humidity`, `precipitation`, `weathercode`, and `cloudcover`. A helper translates those numbers into labels like “cloudy” or “storm” for the background picker.

### Currency Comparison
- Each timezone is mapped to an ISO country code via `pytz` and an optional alias file.
- The country code feeds into RestCountries to find the primary currency.
- Frankfurter’s API returns the historical rate for the given date so we can show `1 source = X target` with the exact rate timestamp.

## Under the Hood (High-Level Architecture)

Component | What it does | Extra notes
--------- | ------------- | -----------
`Tzpy.py` | Launches the wxPython window, wires events, handles user input, owns the theme engine | Depends on `wxPython`, `pytz`, `tzlocal`, plus the two helper modules below
`weather_api.py` | Geocodes the timezone-derived city, fetches hourly weather data, and labels conditions | Uses `requests` for Open-Meteo geocoding + weather endpoints
`currency.py` | Maps timezones to countries, derives currencies, and calls Frankfurter for exchange rates | Uses `requests` and `pytz`
`tz_aliases.txt` | Optional mapping for legacy timezone identifiers so lookups still succeed | Plain text `alias=canonical`

Data flow in one glance:
1. User enters a datetime + timezones.
2. The GUI converts the time, updates the themed background, and displays the string.
3. Weather and currency buttons reuse that context to fetch their respective API data and show formatted summaries.

## Files at a Glance

- **`Tzpy.py`** – Main script. Notable functions:
  - `time_zone_converter` handles the conversion math.
  - `back_fore_ground` and `set_time_bucket_from_time` pick the artwork.
  - `on_convert`, `on_now`, `on_weather`, `on_currency_convert` are the event callbacks.
  - The bottom half declares and positions every widget (absolute layout sized for a 1280×720 window).
- **`weather_api.py`** – Turns a timezone into coordinates, then into weather data. Adds a `condition` string for the background switcher.
- **`currency.py`** – Figures out which currency belongs to each timezone and calls Frankfurter for a `1-unit` comparison.
- **`tz_aliases.txt`** – Handy spot for mapping `US/Eastern`-style legacy IDs to their canonical forms if someone types an older name.

## Tips + Troubleshooting

- `ModuleNotFoundError`: double-check that you installed the dependencies in the same interpreter you use for `python Tzpy.py`.
- Weather errors about “exact hour”: the API expects minute/second to be `00`. The textbox hint reminds you, but validation happens again server-side.
- Currency alias errors: ensure both dropdowns are actual location-based zones (`America/New_York`, not `UTC`). Plain offsets do not map to countries.
- GUI window blank? Watch the PowerShell output—any network errors while loading background art or API data show up there first.

## Ideas for Future Iterations

1. Persist the last selections to a JSON file so the app remembers your previous session.
2. Add amount inputs for the FX card (currently fixed at `1 unit`).
3. Swap the absolute layout for wxPython sizers to support window resizing.
4. Drop in richer condition art (fog, snow, thunder) once the current theme palette is finalized.

Feel free to fork, remix, or file issues if you spot bugs. I’m always down to hear what would make this little dashboard more helpful in a real-world student workflow.
