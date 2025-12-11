"""Desktop helper that fuses timezone conversion with weather lookups."""

from datetime import datetime, time  # Core datetime parsing and comparisons.
import pytz  # Timezone database and conversion helpers.
import wx  # wxPython GUI toolkit.
from tzlocal import get_localzone_name  # OS timezone helper for the "Current Local" button.
import weather_api as wa  # Project weather helpers.

# --- Global UI State ------------------------------------------------------
result = ""  # Most recent converted timestamp shown in the UI.
text_widgets = []  # Static labels whose colours update with the theme.
input_widgets = []  # Inputs that share hint text, fonts, and palette updates.
button_widgets = []  # Buttons grouped for consistent styling.
last_text_mode = "light"  # Remembers which palette was last applied.
bg_bitmap = None  # wx.StaticBitmap instance responsible for the artwork layer.

# --- Background Image System ---
current_time_bucket = "night"          # pre_dawn, sunrise, morning, day, evening, night
current_weather_condition = "clear"    # clear, cloudy, rain, snow, storm

# Catalog mapping (time_bucket, condition) to the art asset used for the backdrop.
# Keeping it as one dictionary lets back_fore_ground perform a single lookup per refresh.
BACKGROUND_IMAGES = {
    # PRE-DAWN / NIGHT BEFORE SUNRISE
    ("pre_dawn", "clear"):  "images/pre_dawn_clear.png",
    ("pre_dawn", "cloudy"): "images/pre_dawn_cloudy.png",
    ("pre_dawn", "rain"):   "images/pre_dawn_rain.png",
    ("pre_dawn", "snow"):   "images/pre_dawn_snow.png",
    ("pre_dawn", "storm"):  "images/pre_dawn_storm.png",
    # SUNRISE
    ("sunrise", "clear"):   "images/morning_clear.png",
    ("sunrise", "cloudy"):  "images/morning_cloudy.png",
    ("sunrise", "rain"):    "images/morning_rain.png",
    ("sunrise", "snow"):    "images/morning_snow.png",
    ("sunrise", "storm"):   "images/morning_storm.png",

    # MORNING – AFTER SUNRISE
    ("morning", "clear"):   "images/after_morning_clear.png",
    ("morning", "cloudy"):  "images/after_morning_cloudy.png",
    ("morning", "rain"):    "images/after_morning_rain.png",
    ("morning", "snow"):    "images/after_morning_snow.png",
    ("morning", "storm"):   "images/after_morning_storm.png",
    # DAYTIME
    ("day", "clear"):       "images/day_clear.png",
    ("day", "cloudy"):      "images/day_cloudy.png",
    ("day", "rain"):        "images/day_rain.png",
    ("day", "snow"):        "images/day_snow.png",
    ("day", "storm"):       "images/day_storm.png",

    # EVENING / SUNSET
    ("evening", "clear"):   "images/evening_clear.png",
    ("evening", "cloudy"):  "images/evening_cloudy.png",
    ("evening", "rain"):    "images/evening_rain.png",
    ("evening", "snow"):    "images/evening_snow.png",
    ("evening", "storm"):   "images/evening_storm.png",

    # NIGHT TIME
    ("night", "clear"):     "images/night_clear.png",
    ("night", "cloudy"):    "images/night_cloudy.png",
    ("night", "rain"):      "images/night_rain.png",
    ("night", "snow"):      "images/night_snow.png",
    ("night", "storm"):     "images/night_storm.png",
}

# Font helper keeps headings consistent without repeating the wx.Font setup.
BASE_FONT_NAME = "Segoe Print"  # Soft handwritten font available on Windows.


def apply_anime_font(widget, size=11, weight=wx.FONTWEIGHT_NORMAL):
    """Apply a playful handwritten font to the given widget."""
    try:
        font = wx.Font(  # Attempt preferred handwritten face first.
            pointSize=size,
            family=wx.FONTFAMILY_SWISS,
            style=wx.FONTSTYLE_NORMAL,
            weight=weight,
            underline=False,
            faceName=BASE_FONT_NAME,
        )
    except Exception:
        font = wx.Font(pointSize=size, family=wx.FONTFAMILY_SWISS, style=wx.FONTSTYLE_NORMAL, weight=weight)  # Fallback if font missing.
    widget.SetFont(font)  # Apply the resolved font to the widget.


def time_zone_converter(time_str, from_tz, to_tz, time_format="%Y-%m-%d %H:%M:%S"):
    """Parse `time_str`, localize it to `from_tz`, then return the formatted value in `to_tz`."""
    from_timezone = pytz.timezone(from_tz)  # Source tz definition used for localization.
    to_timezone = pytz.timezone(to_tz)  # Destination tz definition for conversion target.

    naive_time = datetime.strptime(time_str, time_format)  # Create a naïve datetime from the provided string.
    localized_time = from_timezone.localize(naive_time)  # Bind the naïve datetime to the source tz (handles DST).
    converted_time = localized_time.astimezone(to_timezone)  # Shift that datetime into the destination tz.

    return converted_time.strftime(time_format)  # Return a string using the original format for UI display.

def back_fore_ground(text_mode):
    """Select artwork + text palette, then repaint the backdrop."""

    global bg_bitmap, current_time_bucket, current_weather_condition, last_text_mode
    last_text_mode = text_mode  # Store mode so window resizes can reuse it.

    # Step 1: look up which asset matches the active time bucket + weather tag.
    key = (current_time_bucket, current_weather_condition)
    img_path = BACKGROUND_IMAGES.get(key)

    # Step 2: fall back to the clear-sky variant for that bucket if the combo is missing.
    if img_path is None:
        img_path = BACKGROUND_IMAGES.get((current_time_bucket, "clear"))

    # Step 3: load + scale the bitmap so it always spans the full window.
    if img_path and bg_bitmap is not None:
        try:
            w, h = panel.GetClientSize()  # Ask wx for the current drawable size.

            img = wx.Image(img_path, wx.BITMAP_TYPE_ANY)
            if w > 0 and h > 0:  # wx can report (0, 0) during startup.
                img = img.Scale(w, h, wx.IMAGE_QUALITY_HIGH)

            bmp = wx.Bitmap(img)
            bg_bitmap.SetBitmap(bmp)
            bg_bitmap.SetSize((w, h))
            bg_bitmap.SetPosition((0, 0))
            bg_bitmap.Lower()  # Keep the bitmap behind all interactive widgets.
            panel.Refresh()
        except Exception as e:
            print("Error loading image:", img_path, e)

    # Step 4: paint the panel white so controls stay legible even with dark art.
    if "panel" in globals():
        try:
            panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        except Exception:
            pass


def set_time_bucket_from_time(t_obj):
    """Update time bucket and reapply background."""
    global current_time_bucket

    if time(0, 0, 0) <= t_obj < time(4, 0, 0):
        current_time_bucket = "pre_dawn"  # After midnight but before sunrise glow.
        mode = "light"
    elif time(4, 0, 0) <= t_obj < time(6, 0, 0):
        current_time_bucket = "sunrise"  # Warm tones, sun just peeking out.
        mode = "light"
    elif time(6, 0, 0) <= t_obj < time(10, 0, 0):
        current_time_bucket = "morning"  # Cooler daylight palette.
        mode = "dark"
    elif time(10, 0, 0) <= t_obj < time(17, 0, 0):
        current_time_bucket = "day"  # Bright ambient midday art.
        mode = "dark"
    elif time(17, 0, 0) <= t_obj < time(20, 0, 0):
        current_time_bucket = "evening"  # Sunset / twilight gradients.
        mode = "dark"
    else:
        current_time_bucket = "night"  # Deep night sky.
        mode = "light"

    back_fore_ground(mode)

def time_background_converter_output():
    """Repaint the UI based on the converted time-of-day bucket."""
    if not result:
        return
    try:
        t = datetime.strptime(result, "%Y-%m-%d %H:%M:%S").time()
        set_time_bucket_from_time(t)
    except ValueError:
        return


def time_background_converter_input():
    """Change the background immediately as the user edits the time string."""
    try:
        t = datetime.strptime(inputdt.GetValue(), "%Y-%m-%d %H:%M:%S").time()
        set_time_bucket_from_time(t)
    except ValueError:
        return



def on_now(event):
    """Prefill the controls with the current local timestamp."""
    now = datetime.now()
    inputdt.SetValue(now.strftime("%Y-%m-%d %H:%M:%S"))
    fromtz.SetStringSelection(get_localzone_name())
    time_background_converter_input()
    


def simple_frame(event=None):
    """Sync globals with the latest widget values."""
    global time_str, from_tz, to_tz
    # Read the latest control values so conversions always use current input.
    time_str = inputdt.GetValue()
    time_background_converter_input()  # Update the background preview live while typing.
    from_tz = fromtz.GetStringSelection()
    to_tz = totz.GetStringSelection()


def on_reset(event):
    """Clear inputs and outputs so the next conversion starts fresh."""
    global result, current_weather_condition
    inputdt.SetValue("")
    fromtz.SetSelection(wx.NOT_FOUND)
    totz.SetSelection(wx.NOT_FOUND)
    output.SetLabel("")
    weather_output.SetLabel("")
    result = ""
    current_weather_condition = "clear"
    set_time_bucket_from_time(datetime.now().time())
        
def on_weather(event):
    """Validate inputs, fetch hourly weather for the target zone, and render a compact summary."""
    dt_str_local = inputdt.GetValue().strip()  # Datetime string typed in the text box.
    if not dt_str_local:
        weather_output.SetLabel("Error: Enter datetime (YYYY-MM-DD HH:MM:SS)")
        return

    tz_name = totz.GetStringSelection()  # Target timezone drives the weather lookup.
    if not tz_name:
        weather_output.SetLabel("Error: Select a target timezone (To TZ) for weather.")
        return

    try:
        datetime.strptime(dt_str_local, "%Y-%m-%d %H:%M:%S")  # Format validation before hitting the API.
    except ValueError:
        weather_output.SetLabel("Error: Invalid datetime format.")
        return

    try:
        weather = wa.get_weather_for_datetime(dt_str_local, tz_name)  # Delegate to Open-Meteo helper.

        # Save the parsed condition tag so the background can mirror rain/snow/storm visuals.
        global current_weather_condition
        current_weather_condition = weather.get("condition", "clear")

        # Reapply background so visuals match the reported condition.
        try:
            if result:
                t_obj = datetime.strptime(result, "%Y-%m-%d %H:%M:%S").time()
            else:
                t_obj = datetime.strptime(dt_str_local, "%Y-%m-%d %H:%M:%S").time()
            set_time_bucket_from_time(t_obj)
        except Exception:
            pass
        display_time = weather["time"].replace("T", " ")  # Present ISO string in a UI-friendly form.
        msg = (
            f"🌤 {weather['city']}, {weather['country']} @ {display_time}\n"
            f"🌡 Temp: {weather['temperature']}°C   "
            f"💧 Humidity: {weather['humidity']}%   \n"
            # f"🌧 Precip: {weather['precipitation']} mm\n"
            f"🌈 Condition: {weather['condition'].capitalize()}"
        )
        weather_output.SetLabel(msg)
    except Exception as e:
        weather_output.SetLabel(f"Weather error: {e}")
        
def on_convert(event):
    """Run the main conversion and refresh the display."""
    simple_frame()
    global result

    try:
        result = time_zone_converter(time_str, from_tz, to_tz)
        output.SetLabel(f'📍 {from_tz} : {time_str} \n 🎯 {to_tz} : {result}')
        time_background_converter_output()
    except Exception:
        output.SetLabel("Error: Invalid input or timezone")
def on_resize(event):
    back_fore_ground(last_text_mode)  # Rescale background art to the new panel dimensions.
    event.Skip()  # Allow default wx handling to continue.


# ---------------- UI SETUP (wxPython) ---------------- #

# Layout constants for the fixed 1440x810 frame:
# - FRAME_WIDTH/HEIGHT keep the background art scaling predictable.
# - LEFT_MARGIN, CONTROL_WIDTH/HEIGHT, and COLUMN_GAP place the input column.
# - RIGHT_BUTTON_X is derived so action buttons line up with the inputs.
# - BUTTON_WIDTH/HEIGHT give every button the same hit area.
# - RIGHT_MARGIN/BOTTOM_MARGIN anchor the reset button in the lower-right corner.
# - DISPLAY_WIDTH controls how wide the multiline output labels can grow.
FRAME_WIDTH = 1440
FRAME_HEIGHT = 810
LEFT_MARGIN = 120
CONTROL_WIDTH = 250
CONTROL_HEIGHT = 36
COLUMN_GAP = 90
RIGHT_BUTTON_X = LEFT_MARGIN + CONTROL_WIDTH + COLUMN_GAP - 60
BUTTON_WIDTH = 220
BUTTON_HEIGHT = 42
RIGHT_MARGIN = 60
BOTTOM_MARGIN = 60
DISPLAY_WIDTH = 0

# Preload all IANA zones so both dropdowns have identical lists.
timezones = pytz.all_timezones
app = wx.App(False)
frame = wx.Frame(
    None,
    title="Time & Weather Tool",
    size=(FRAME_WIDTH, FRAME_HEIGHT),
    style=wx.DEFAULT_FRAME_STYLE
          & ~( wx.MAXIMIZE_BOX | wx.RESIZE_BORDER)
)
panel = wx.Panel(frame, style=wx.SIMPLE_BORDER)
panel.SetDoubleBuffered(True)
bg_bitmap = wx.StaticBitmap(panel, -1, wx.Bitmap(1, 1), pos=(0, 0))
bg_bitmap.Lower()  # Put it behind all other widgets
panel.Bind(wx.EVT_SIZE, on_resize)

# Time / Date
show1 = wx.StaticText(panel, label="ENTER DATE AND TIME", pos=(LEFT_MARGIN, 70))
inputdt = wx.TextCtrl(panel, pos=(LEFT_MARGIN, 108), size=(CONTROL_WIDTH, CONTROL_HEIGHT), style=wx.SIMPLE_BORDER)
inputdt.SetHint("YYYY-MM-DD HH:MM:SS")
nowtime = wx.Button(
    panel,
    label="CURRENT LOCAL",
    pos=(RIGHT_BUTTON_X, 106),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)

# Timezones
show4 = wx.StaticText(panel, label="Select Source and Target", pos=(LEFT_MARGIN, 190))
fromtz = wx.Choice(panel, choices=timezones, pos=(LEFT_MARGIN, 228), size=(CONTROL_WIDTH, 36), style=wx.BORDER_SUNKEN)
totz = wx.Choice(panel, choices=timezones, pos=(LEFT_MARGIN, 278), size=(CONTROL_WIDTH, 36), style=wx.BORDER_SUNKEN)

convert = wx.Button(
    panel,
    label="CONVERT TIME",
    pos=(RIGHT_BUTTON_X, 276),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)
reset_btn = wx.Button(
    panel,
    label="RESET",
    pos=(FRAME_WIDTH - RIGHT_MARGIN - BUTTON_WIDTH, FRAME_HEIGHT - BOTTOM_MARGIN - BUTTON_HEIGHT),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)
show5 = wx.StaticText(panel, label="RESULT ↓", pos=(LEFT_MARGIN, 352), style=wx.SIMPLE_BORDER)
output = wx.StaticText(panel, label="", pos=(LEFT_MARGIN, 390), size=(DISPLAY_WIDTH, 0), style=wx.SIMPLE_BORDER)

# Weather UI
show_weather = wx.StaticText(panel, label="WEATHER", pos=(LEFT_MARGIN, 476))
weather_btn = wx.Button(
    panel,
    label="GET WEATHER",
    pos=(RIGHT_BUTTON_X, 466),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)
weather_output = wx.StaticText(panel, label="", pos=(LEFT_MARGIN, 516), size=(DISPLAY_WIDTH, 0), style=wx.SIMPLE_BORDER)


# Bindings
inputdt.Bind(wx.EVT_TEXT, simple_frame)
fromtz.Bind(wx.EVT_CHOICE, simple_frame)
totz.Bind(wx.EVT_CHOICE, simple_frame)
convert.Bind(wx.EVT_BUTTON, on_convert)
reset_btn.Bind(wx.EVT_BUTTON, on_reset)
nowtime.Bind(wx.EVT_BUTTON, on_now)
weather_btn.Bind(wx.EVT_BUTTON, on_weather)

# Widgets participating in theme swaps
text_widgets = [  # Static labels and outputs that follow theme colours.
    show1,
    show4,
    show5,
    output,
    show_weather,
    weather_output,
]
input_widgets = [  # Controls that accept user input.
    inputdt,
    fromtz,
    totz,
]
button_widgets = [  # Action buttons that need consistent theming.
    convert,
    reset_btn,
    nowtime,
    weather_btn,
]

for widget in text_widgets:
    apply_anime_font(widget, size=12, weight=wx.FONTWEIGHT_MEDIUM)  # Use a slightly larger handwriting font for readability.

for widget in input_widgets:
    apply_anime_font(widget, size=11)  # Keep inputs compact but on-theme.

for widget in button_widgets:
    apply_anime_font(widget, size=11, weight=wx.FONTWEIGHT_BOLD)  # Bold buttons for emphasis.

apply_anime_font(output, size=13, weight=wx.FONTWEIGHT_MEDIUM)  # Highlight the main conversion result.
apply_anime_font(weather_output, size=12)  # Weather summary uses slightly larger text.


frame.Show()  # Display the fully configured window.

# Force initial background + text colours so buttons are visible
set_time_bucket_from_time(datetime.now().time())  # Kick off theme logic using the current local time bucket.

app.MainLoop()  # Enter the wxPython event loop.


# # Simple user input (legacy CLI demo)
# print("=== pytz Time Zone Converter ===")  # Display a heading when running via console.
# print("Example: 2024-01-15 14:30:00")  # Show an example of the expected datetime format.

# time_str = input("Enter time (YYYY-MM-DD HH:MM:SS): ")  # Prompt for the source datetime string.
# from_tz = input("Enter source timezone (e.g., US/Eastern): ")  # Prompt for the source timezone name.
# to_tz = input("Enter target timezone (e.g., Asia/Tokyo): ")  # Prompt for the destination timezone name.

# result = time_zone_converter(time_str, from_tz, to_tz)  # Perform the conversion using console input.

# print(f"\n🔄 Conversion Result:")  # Label the output section for clarity.
# print(f"📍 {from_tz}: {time_str}")  # Echo the original timezone and time.
# print(f"🎯 {to_tz}: {result}")  # Echo the converted timezone and time.
