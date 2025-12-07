from datetime import datetime, time  # Core datetime parsing and comparisons.
import pytz  # Timezone database and conversion helpers.
import wx  # wxPython GUI toolkit.
from tzlocal import get_localzone_name  # OS timezone helper for the "Current Local" button.
import weather_api as wa  # Project weather helpers.
import currency as cu  # Project currency helpers.

result = ""  # Last converted timestamp shown in the UI.
text_widgets = []  # Reserved hooks for static text theme updates.
input_widgets = []  # Reserved hooks for input/theme updates.
button_widgets = []  # Reserved hooks for button-specific theming.
last_text_mode = "light"
# --- Background Image System ---
bg_bitmap = None

# Time-of-day bucket + rain flag
current_time_bucket = "night"
current_weather_is_rainy = False

# Mapping (time_bucket, rainy?) -> image path
BACKGROUND_IMAGES = {
    ("pre_dawn", False): "images/night_clear_1.png",
    ("pre_dawn", True):  "images/night_rain_1.png",

    ("sunrise", False):  "images/morning_clear_1.png",
    ("sunrise", True):   "images/morning_rain_1.png",

    ("morning", False):  "images/morning_clear_1.png",
    ("morning", True):   "images/morning_rain_1.png",

    ("day", False):      "images/day_clear_1.png",
    ("day", True):       "images/day_rain_1.png",

    ("evening", False):  "images/evening_clear_1.png",
    ("evening", True):   "images/evening_rain_1.png",

    ("night", False):    "images/night_clear_1.png",
    ("night", True):     "images/night_rain_1.png",
}

# Anime-inspired font styling
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
    """Apply background image and UI text colors."""
    global bg_bitmap, current_time_bucket, current_weather_is_rainy, last_text_mode
    last_text_mode = text_mode
    key = (current_time_bucket, current_weather_is_rainy)
    img_path = BACKGROUND_IMAGES.get(key)

    if img_path and bg_bitmap is not None:
        try:
            # Get current panel size
            w, h = panel.GetClientSize()

            img = wx.Image(img_path, wx.BITMAP_TYPE_ANY)
            # Avoid 0-size crashes on initial load
            if w > 0 and h > 0:
                img = img.Scale(w, h, wx.IMAGE_QUALITY_HIGH)

            bmp = wx.Bitmap(img)
            bg_bitmap.SetBitmap(bmp)
            bg_bitmap.SetSize((w, h))
            bg_bitmap.SetPosition((0, 0))
            bg_bitmap.Lower()
            panel.Refresh()
        except Exception as e:
            print("Error loading image:", img_path, e)

    # Keep the main panel white regardless of the active mode for a clean base layer.
    if "panel" in globals():
        try:
            panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        except Exception:
            pass


def set_time_bucket_from_time(t_obj):
    """Update time bucket and reapply background."""
    global current_time_bucket

    if time(0, 0, 0) <= t_obj < time(4, 0, 0):
        current_time_bucket = "pre_dawn"
        mode = "light"
    elif time(4, 0, 0) <= t_obj < time(6, 0, 0):
        current_time_bucket = "sunrise"
        mode = "light"
    elif time(6, 0, 0) <= t_obj < time(10, 0, 0):
        current_time_bucket = "morning"
        mode = "dark"
    elif time(10, 0, 0) <= t_obj < time(17, 0, 0):
        current_time_bucket = "day"
        mode = "dark"
    elif time(17, 0, 0) <= t_obj < time(20, 0, 0):
        current_time_bucket = "evening"
        mode = "dark"
    else:
        current_time_bucket = "night"
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
    


def simple_frame():
    """Sync globals with the latest widget values."""
    global time_str, from_tz, to_tz
    time_str = inputdt.GetValue()  # Cache the raw datetime string from the text control.
    time_background_converter_input()  # Nudge the background preview each time the field changes.
    from_tz = fromtz.GetStringSelection()  # Remember the currently chosen source timezone.
    to_tz = totz.GetStringSelection()  # Remember the currently chosen destination timezone.
    
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
        # Update raining status
        global current_weather_is_rainy
        current_weather_is_rainy = weather["precipitation"] > 0

        # Reapply background with rain condition
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
            f"💧 Humidity: {weather['humidity']}%   "
            f"🌧 Precip: {weather['precipitation']} mm"
        )
        weather_output.SetLabel(msg)
    except Exception as e:
        weather_output.SetLabel(f"Weather error: {e}")
        
def on_currency_convert(event):
    """Translate both timezones to currencies and show a 1-unit historical conversion."""
    from_tz_raw = fromtz.GetStringSelection()  # Source timezone selected by the user.
    to_tz_raw = totz.GetStringSelection()  # Destination timezone selected by the user.

    if not from_tz_raw or not to_tz_raw:
        currency_output.SetLabel("Error: Select both source and target timezones first.")
        return

    dt_str_local = inputdt.GetValue().strip()  # Reuse the same datetime to choose the FX date.
    if not dt_str_local:
        currency_output.SetLabel("Error: Enter datetime (YYYY-MM-DD HH:MM:SS) for rate date.")
        return

    try:
        dt_obj = datetime.strptime(dt_str_local, "%Y-%m-%d %H:%M:%S")  # Parse once so we can extract the date.
        date_for_rate = dt_obj.date().isoformat()  # YYYY-MM-DD string consumed by the FX API.
    except ValueError:
        currency_output.SetLabel("Error: Invalid datetime format.")
        return

    try:
        from_cur = cu.get_currency_from_timezone(from_tz_raw)  # Map timezone -> country -> currency.
        to_cur = cu.get_currency_from_timezone(to_tz_raw)
    except Exception as e:
        currency_output.SetLabel(f"Currency mapping error: {e}")
        return

    try:
        amount = 1.0  # Fixed comparison amount shown in the UI.
        converted, date_used = cu.convert_currency(amount, from_cur, to_cur, date_for_rate)  # Call Frankfurter helper.
        msg = (
            f"💱 Based on timezones & date:\n"
            f"{from_tz_raw} -> {from_cur}   |   {to_tz_raw} -> {to_cur}\n"
            f"Date: {date_for_rate}\n\n"
            f"1 {from_cur} = {converted:.6f} {to_cur}  (rate date from API: {date_used})"
        )
        currency_output.SetLabel(msg)
    except Exception as e:
        currency_output.SetLabel(f"Currency error: {e}")
def on_convert(event):
    """Run the main conversion and refresh the display."""
    simple_frame()
    global result

    try:
        result = time_zone_converter(time_str, from_tz, to_tz)
        output.SetLabel(f'📍 {from_tz} : {time_str}  ->  🎯 {to_tz} : {result}')
        time_background_converter_output()
    except Exception:
        output.SetLabel("Error: Invalid input or timezone")
def on_resize(event):
    back_fore_ground(last_text_mode)  # Rescale background art to the new panel dimensions.
    event.Skip()  # Allow default wx handling to continue.


# ---------------- UI SETUP (wxPython) ---------------- #

LEFT_MARGIN = 80
CONTROL_WIDTH = 420
CONTROL_HEIGHT = 32
RIGHT_BUTTON_X = LEFT_MARGIN + CONTROL_WIDTH + 70
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 38
DISPLAY_WIDTH = 920

timezones = pytz.all_timezones  # Populate dropdowns with every IANA zone.
app = wx.App(False)
frame = wx.Frame(
    None,
    title="Time, Weather & Currency Tool",
    size=(1280, 720),
    style=wx.DEFAULT_FRAME_STYLE
          & ~( wx.MAXIMIZE_BOX | wx.RESIZE_BORDER)
)
panel = wx.Panel(frame, style=wx.SIMPLE_BORDER)
panel.SetDoubleBuffered(True)
bg_bitmap = wx.StaticBitmap(panel, -1, wx.Bitmap(1, 1), pos=(0, 0))
bg_bitmap.Lower()  # Put it behind all other widgets
panel.Bind(wx.EVT_SIZE, on_resize)

# Time / Date
show1 = wx.StaticText(panel, label="ENTER DATE & TIME", pos=(LEFT_MARGIN, 40))
inputdt = wx.TextCtrl(panel, pos=(LEFT_MARGIN, 72), size=(CONTROL_WIDTH, CONTROL_HEIGHT), style=wx.SIMPLE_BORDER)
inputdt.SetHint("YYYY-MM-DD HH:MM:SS e.g. 2007-02-22 12:00:00")
nowtime = wx.Button(
    panel,
    label="CURRENT LOCAL",
    pos=(RIGHT_BUTTON_X, 70),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)

# Timezones
show4 = wx.StaticText(panel, label="Select Source and Target Timezones", pos=(LEFT_MARGIN, 135))
fromtz = wx.Choice(panel, choices=timezones, pos=(LEFT_MARGIN, 165), size=(CONTROL_WIDTH, 34), style=wx.BORDER_SUNKEN)
totz = wx.Choice(panel, choices=timezones, pos=(LEFT_MARGIN, 210), size=(CONTROL_WIDTH, 34), style=wx.BORDER_SUNKEN)

convert = wx.Button(
    panel,
    label="CONVERT TIME",
    pos=(RIGHT_BUTTON_X, 208),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)
show5 = wx.StaticText(panel, label="CONVERTED TIME WILL APPEAR HERE ↓", pos=(LEFT_MARGIN, 270), style=wx.SIMPLE_BORDER)
output = wx.StaticText(panel, label="", pos=(LEFT_MARGIN, 302), size=(DISPLAY_WIDTH, 40), style=wx.SIMPLE_BORDER)

# Weather UI
show_weather = wx.StaticText(panel, label="WEATHER", pos=(LEFT_MARGIN, 360))
weather_btn = wx.Button(
    panel,
    label="GET WEATHER",
    pos=(RIGHT_BUTTON_X, 350),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)
weather_output = wx.StaticText(panel, label="", pos=(LEFT_MARGIN, 395), size=(DISPLAY_WIDTH, 90), style=wx.SIMPLE_BORDER)

# Currency UI (automatic from timezones + historical)
show_currency = wx.StaticText(panel, label="CURRENCY", pos=(LEFT_MARGIN, 510))
currency_btn = wx.Button(
    panel,
    label="COMPARE 1 UNIT",
    pos=(RIGHT_BUTTON_X, 500),
    size=(BUTTON_WIDTH, BUTTON_HEIGHT),
    style=wx.BORDER_RAISED,
)
currency_output = wx.StaticText(panel, label="", pos=(LEFT_MARGIN, 545), size=(DISPLAY_WIDTH, 110), style=wx.SIMPLE_BORDER)

# Bindings
inputdt.Bind(wx.EVT_TEXT, simple_frame)
fromtz.Bind(wx.EVT_CHOICE, simple_frame)
totz.Bind(wx.EVT_CHOICE, simple_frame)
convert.Bind(wx.EVT_BUTTON, on_convert)
nowtime.Bind(wx.EVT_BUTTON, on_now)
weather_btn.Bind(wx.EVT_BUTTON, on_weather)
currency_btn.Bind(wx.EVT_BUTTON, on_currency_convert)

# Widgets participating in theme swaps
text_widgets = [  # Static labels and outputs that follow theme colours.
    show1,
    show4,
    show5,
    output,
    show_weather,
    weather_output,
    show_currency,
    currency_output,
]
input_widgets = [  # Controls that accept user input.
    inputdt,
    fromtz,
    totz,
]
button_widgets = [  # Action buttons that need consistent theming.
    convert,
    nowtime,
    weather_btn,
    currency_btn,
]

for widget in text_widgets:
    apply_anime_font(widget, size=12, weight=wx.FONTWEIGHT_MEDIUM)  # Use a slightly larger handwriting font for readability.

for widget in input_widgets:
    apply_anime_font(widget, size=11)  # Keep inputs compact but on-theme.

for widget in button_widgets:
    apply_anime_font(widget, size=11, weight=wx.FONTWEIGHT_BOLD)  # Bold buttons for emphasis.

apply_anime_font(output, size=13, weight=wx.FONTWEIGHT_MEDIUM)  # Highlight the main conversion result.
apply_anime_font(weather_output, size=12)  # Weather summary uses slightly larger text.
apply_anime_font(currency_output, size=12)  # Currency summary matches weather text size.


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
