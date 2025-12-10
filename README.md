# PythonJackfruit

> Final project submission prepared for my Computer Science teacher. The goal was to practice GUI work while combining API data sources in one workflow.

## Project Overview

PythonJackfruit is a desktop helper that lets the user convert a datetime between two time zones and immediately request weather information for the target zone. The interface is built with wxPython, and background artwork shifts automatically to match the time bucket (night, sunrise, day, etc.) and reported weather condition. This keeps the UI visual but still focused on the data the assignment asked for.

## Learning Targets

- Reinforce Python module design by separating the GUI (`Tzpy.py`) from the API helper (`weather_api.py`).
- Practice calling public web APIs (Open-Meteo) and handling validation/edge cases.
- Apply coordinate geometry from class (absolute positioning) to place controls on a 16:9 frame.

## Feature Summary

1. Time zone conversion backed by `pytz`, including daylight-saving adjustments.
2. "Current Local" shortcut pulls the machine’s zone using `tzlocal` to reduce typing mistakes.
3. Weather lookup reuses the converted context so the user does not re-enter data.
4. Dynamic background system selects artwork based on both time bucket and reported condition.

## How to Run the Program

1. Install Python 3.10 or newer.
2. Install the required packages:
   ```powershell
   pip install wxPython pytz tzlocal requests
   ```
3. Run the GUI from the repository root:
   ```powershell
   python Tzpy.py
   ```
4. Enter a datetime in the format `YYYY-MM-DD HH:MM:SS`. Minutes and seconds should be `00` so they line up with the hourly weather data.
5. Choose the source and destination time zones, then press **Convert Time**.
6. Press **Get Weather** to fetch the hourly weather summary for the destination.

## Testing and Verification

- Manual tests covered conversions between local time, UTC, and a distant zone (e.g., Asia/Tokyo) to check DST handling.
- Weather queries were issued for both future and past timestamps to confirm the helper switches between forecast and archive endpoints correctly.
- Background images were checked by forcing each time bucket through the input field.

## Reflection and Next Steps

- **What worked:** Keeping the GUI logic in one file and the API logic in another made debugging easier. Using absolute coordinates simplified the layout phase for this assignment.
- **What I would improve next:** add input persistence so the program remembers the last-used time zones, and replace the absolute layout with wxPython sizers for better resizing support.

Thank you for reviewing this project. I am happy to walk through the code or demonstrate the workflow in class if needed.
