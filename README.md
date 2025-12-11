# PythonJackfruit

> Computer Science project submission — a wxPython desktop assistant that combines time-zone conversion with weather insights in one interface.

## 📚 Assignment Summary
PythonJackfruit demonstrates how a Python GUI can orchestrate multiple data sources inside a single workflow. The objective was to design and code a desktop tool that:
- Converts datetimes between arbitrary IANA time zones.
- Fetches real-world weather data for the conversion target.
- Reflects time-of-day and weather conditions through responsive background art.

## 🎯 Learning Outcomes
- Apply event-driven programming concepts using wxPython widgets and bindings.
- Separate responsibilities across modules: `Tzpy.py` for presentation logic, `weather_api.py` for data acquisition.
- Practice calling Open-Meteo’s Geocoding + Forecast/Archive APIs and handling validation errors gracefully.
- Strengthen UX considerations by pairing data displays with visual cues (dynamic backgrounds).

## ✨ Feature Overview
- **Time-Zone Conversion:** `pytz` handles localization and daylight-saving transitions so outputs remain accurate year-round.
- **Weather Lookup:** Leverages Open-Meteo endpoints to summarize temperature, humidity, precipitation, and conditions that match the converted time.
- **Dynamic Animated-Style Background:** Time buckets (pre-dawn, sunrise, morning, day, evening, night) cross-referenced with weather tags (clear, cloudy, rain, snow, storm) drive the background artwork selection.
- **GUI System:** wxPython powers the 1440×810 interface, complete with custom fonts, instant field validation, and large buttons for classroom demonstrations.

## 🏗 How It Works (Architecture)
Component | Role | Key Libraries
--------- | ---- | ------------
`Tzpy.py` | Main window, widget layout, conversion logic, background engine, event handlers (`on_now`, `on_convert`, `on_weather`, `on_reset`). | `wxPython`, `pytz`, `tzlocal`
`weather_api.py` | Converts timezone strings into coordinates, calls Open-Meteo’s weather endpoints, classifies conditions for the UI theme. | `requests`

Data Flow:
1. User enters a datetime and chooses source/target zones.
2. `time_zone_converter` localizes the input, performs the conversion, and updates the result label.
3. Weather lookups reuse the target zone to query Open-Meteo; responses populate the summary panel and feed the background selector.
4. `set_time_bucket_from_time` + `current_weather_condition` determine which background image displays.

## 🛠 Requirements & Installation
- Python 3.10+
- Packages: `wxPython`, `pytz`, `tzlocal`, `requests`

```powershell
pip install wxPython pytz tzlocal requests
```

## 🚀 Running the Application
```powershell
python Tzpy.py
```

### Example Usage
1. Enter `2025-05-20 08:00:00` in the datetime field (minutes/seconds should be `00` to match hourly weather data).
2. Set **From TZ** to `US/Eastern` and **To TZ** to `Asia/Tokyo`.
3. Click **Convert Time** to view the localized result.
4. Click **Get Weather** to fetch forecast/archived weather for Tokyo at the specified time.
5. Watch the background artwork shift to a morning/rain scene if the API reports rain.


## ✅ Testing & Verification
- Manually validated conversions across multiple continents and DST boundaries.
- Weather lookups tested for both historical and future timestamps to ensure the correct Open-Meteo endpoint is chosen.
- Background transitions exercised by forcing each time bucket through the input helper.

## ⚠️ Problems Faced
- **Weather API hour alignment:** Open-Meteo’s hourly data forced the minutes/seconds to stay at `00`; forgetting this triggered API errors until I added stricter input hints and validation.
- **Timezone → location mapping:** translating IANA zones like `America/Argentina/Buenos_Aires` into a clean city name occasionally failed; I added fallback strings and error messages for unrecognized mappings.
- **Background asset scaling:** large PNGs flickered while resizing; enabling double-buffering on the wx panel and caching the bitmap resolved the redraw artifacts.
- **Transparent text experiments:** a custom `TransparentText` control caused wx assertions on some machines, so I reverted to `wx.StaticText` and focused on color contrast instead.
- **Event signatures:** methods bound to widget events (like `simple_frame`) initially lacked the `event` parameter, leading to `TypeError` until I allowed optional arguments.

##  Reflection / What I Learned
Building this project taught me how valuable clean separation between GUI code and API helpers can be. I also gained confidence in handling asynchronous-style workflows inside a synchronous desktop app, especially when dealing with validation, error messages, and user feedback. Balancing visuals (dynamic art) with functionality gave me practice aligning user experience goals with software requirements.

- While developing `weather_api.py`, I consulted internet documentation and tutorials to learn the correct sequence for Open-Meteo geocoding, forecast, and archive calls before adapting the logic to my project.
- For the bitmap scaling and double-buffered background layer, I referenced online wxPython examples to understand how to keep transitions smooth and avoid flicker.

## 🔮 Future Improvements
1. Persist the last-used settings so the app remembers my previous session.
2. Replace absolute positioning with wxPython sizers to support window resizing.
3. Add cached weather responses to reduce repeated API calls during testing.
4. Include animated transitions when switching backgrounds for a smoother presentation feel.

## 🙏 Acknowledgements
- Open-Meteo for providing free Geocoding and Forecast/Archive APIs.
- My Computer Science teacher for the rubric and guidance throughout the assignment.

Thank you for reviewing PythonJackfruit. 
