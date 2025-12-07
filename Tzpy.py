from datetime import datetime, time  # Core datetime parsing and comparisons.
import pytz  # Timezone database and conversion helpers.
import wx  # wxPython GUI toolkit.
from tzlocal import get_localzone_name  # OS timezone helper for the "Current Local" button.
import weather_api as wa  # Project weather helpers.
import currency as cu  # Project currency helpers.

result = ""  # Last converted timestamp shown in the UI.
text_widgets = []  # Reserved hooks for theme updates.
input_widgets = []  # Reserved hooks for theme updates.


def time_zone_converter(time_str, from_tz, to_tz, time_format="%Y-%m-%d %H:%M:%S"):
    """Parse `time_str`, localize it to `from_tz`, then return the formatted value in `to_tz`."""
    from_timezone = pytz.timezone(from_tz)  # Source tz definition used for localization.
    to_timezone = pytz.timezone(to_tz)  # Destination tz definition for conversion target.

    naive_time = datetime.strptime(time_str, time_format)  # Create a naïve datetime from the provided string.
    localized_time = from_timezone.localize(naive_time)  # Bind the naïve datetime to the source tz (handles DST).
    converted_time = localized_time.astimezone(to_timezone)  # Shift that datetime into the destination tz.

    return converted_time.strftime(time_format)  # Return a string using the original format for UI display.

def back_fore_ground(bg_color, text_mode):
    """Paint the panel and widgets using a day/night palette."""
    panel.SetBackgroundColour(bg_color)  # Apply the global backdrop color.
    if text_mode == "light":
        text_color = wx.Colour(245, 245, 245)  # Light text for labels.
        item_text = wx.Colour(25, 25, 25)  # Dark text for inputs.
        item_bg = wx.Colour(250, 250, 250)  # Soft input background.
    else:
        text_color = wx.Colour(32, 32, 32)  # Dark labels for bright backgrounds.
        item_text = wx.Colour(25, 25, 25)  # Matching dark text for inputs.
        item_bg = wx.Colour(255, 255, 255)  # Bright input background.

    for text in texts:
        text.SetForegroundColour(text_color)  # Update every label/button with the chosen color.

    for item in variables:
        item.SetForegroundColour(item_text)  # Sync interactive text color.
        item.SetBackgroundColour(item_bg)  # Sync interactive background color.

    panel.Refresh()  # Force redraw so colors take effect immediately.


def time_background_converter_output():
    """Repaint the UI based on the converted time-of-day bucket."""
    if not result:
        return
    try:
        time_result = datetime.strptime(result, "%Y-%m-%d %H:%M:%S").time()
    except ValueError:
        return

    if time(0, 0, 0) <= time_result < time(4, 0, 0):
        back_fore_ground(wx.Colour(6, 10, 28), "light")
    elif time(4, 0, 0) <= time_result < time(6, 0, 0):
        back_fore_ground(wx.Colour(28, 45, 85), "light")
    elif time(6, 0, 0) <= time_result < time(8, 0, 0):
        back_fore_ground(wx.Colour(250, 189, 120), "dark")
    elif time(8, 0, 0) <= time_result < time(10, 0, 0):
        back_fore_ground(wx.Colour(255, 209, 145), "dark")
    elif time(10, 0, 0) <= time_result < time(12, 0, 0):
        back_fore_ground(wx.Colour(255, 234, 185), "dark")
    elif time(12, 0, 0) <= time_result < time(15, 0, 0):
        back_fore_ground(wx.Colour(240, 244, 220), "dark")
    elif time(15, 0, 0) <= time_result < time(17, 0, 0):
        back_fore_ground(wx.Colour(248, 196, 130), "dark")
    elif time(17, 0, 0) <= time_result < time(19, 0, 0):
        back_fore_ground(wx.Colour(252, 140, 90), "dark")
    elif time(19, 0, 0) <= time_result < time(22, 0, 0):
        back_fore_ground(wx.Colour(54, 34, 70), "light")
    else:
        back_fore_ground(wx.Colour(8, 6, 26), "light")

def time_background_converter_input():
    """Change the background immediately as the user edits the time string."""
    try:
        time_input = datetime.strptime(inputdt.GetValue(), "%Y-%m-%d %H:%M:%S").time()
    except ValueError:
        return

    if time(0, 0, 0) <= time_input < time(4, 0, 0):
        back_fore_ground(wx.Colour(6, 10, 28), "light")
    elif time(4, 0, 0) <= time_input < time(6, 0, 0):
        back_fore_ground(wx.Colour(28, 45, 85), "light")
    elif time(6, 0, 0) <= time_input < time(8, 0, 0):
        back_fore_ground(wx.Colour(250, 189, 120), "dark")
    elif time(8, 0, 0) <= time_input < time(10, 0, 0):
        back_fore_ground(wx.Colour(255, 209, 145), "dark")
    elif time(10, 0, 0) <= time_input < time(12, 0, 0):
        back_fore_ground(wx.Colour(255, 234, 185), "dark")
    elif time(12, 0, 0) <= time_input < time(15, 0, 0):
        back_fore_ground(wx.Colour(240, 244, 220), "dark")
    elif time(15, 0, 0) <= time_input < time(17, 0, 0):
        back_fore_ground(wx.Colour(248, 196, 130), "dark")
    elif time(17, 0, 0) <= time_input < time(19, 0, 0):
        back_fore_ground(wx.Colour(252, 140, 90), "dark")
    elif time(19, 0, 0) <= time_input < time(22, 0, 0):
        back_fore_ground(wx.Colour(54, 34, 70), "light")
    else:
        back_fore_ground(wx.Colour(8, 6, 26), "light")


def on_now(event):
    """Prefill the controls with the current local timestamp."""
    now = datetime.now()
    inputdt.SetValue(now.strftime("%Y-%m-%d %H:%M:%S"))
    fromtz.SetStringSelection(get_localzone_name())
    time_background_converter_input()
    


def simple_frame():
    """Sync globals with the latest widget values."""
    global time_str, from_tz, to_tz
    time_str = inputdt.GetValue()
    time_background_converter_input()
    from_tz = fromtz.GetStringSelection()
    to_tz = totz.GetStringSelection()
    
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


# ---------------- UI SETUP (wxPython) ---------------- #

timezones = pytz.all_timezones  # Populate dropdowns with every IANA zone.
app = wx.App(False)
frame = wx.Frame(
    None,
    title="Time, Weather & Currency Tool",
    size=(750, 780),
    style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
)
panel = wx.Panel(frame, style=wx.SIMPLE_BORDER)

# Time / Date
show1 = wx.StaticText(panel, label="ENTER DATE & TIME", pos=(240, 55))
inputdt = wx.TextCtrl(panel, pos=(220, 85), size=(280, 25), style=wx.SIMPLE_BORDER)
inputdt.SetHint("YYYY-MM-DD HH:MM:SS e.g. 2007-02-22 12:00:00")
nowtime = wx.Button(panel, label="CURRENT LOCAL", pos=(290, 120), size=(120, 30), style=wx.BORDER_RAISED)

# Timezones
show4 = wx.StaticText(panel, label="Select Source and Target Timezones", pos=(235, 170))
fromtz = wx.Choice(panel, choices=timezones, pos=(220, 200), size=(280, 30), style=wx.BORDER_SUNKEN)
totz = wx.Choice(panel, choices=timezones, pos=(220, 240), size=(280, 30), style=wx.BORDER_SUNKEN)

convert = wx.Button(panel, label="CONVERT TIME", pos=(290, 280), size=(120, 30), style=wx.BORDER_RAISED)
show5 = wx.StaticText(panel, label="CONVERTED TIME WILL APPEAR HERE ↓", pos=(230, 320), style=wx.SIMPLE_BORDER)
output = wx.StaticText(panel, label="", pos=(50, 350), size=(650, 30), style=wx.SIMPLE_BORDER)

# Weather UI
show_weather = wx.StaticText(panel, label="WEATHER (Uses target timezone city)", pos=(240, 390))
weather_btn = wx.Button(panel, label="GET WEATHER", pos=(290, 420), size=(120, 30), style=wx.BORDER_RAISED)
weather_output = wx.StaticText(panel, label="", pos=(50, 460), size=(650, 60), style=wx.SIMPLE_BORDER)

# Currency UI (automatic from timezones + historical)
show_currency = wx.StaticText(panel, label="CURRENCY (From timezones' countries, with history)", pos=(180, 535))
currency_btn = wx.Button(panel, label="COMPARE 1 UNIT", pos=(290, 565), size=(120, 30), style=wx.BORDER_RAISED)
currency_output = wx.StaticText(panel, label="", pos=(50, 605), size=(650, 100), style=wx.SIMPLE_BORDER)

# Bindings
inputdt.Bind(wx.EVT_TEXT, simple_frame)
fromtz.Bind(wx.EVT_CHOICE, simple_frame)
totz.Bind(wx.EVT_CHOICE, simple_frame)
convert.Bind(wx.EVT_BUTTON, on_convert)
nowtime.Bind(wx.EVT_BUTTON, on_now)
weather_btn.Bind(wx.EVT_BUTTON, on_weather)
currency_btn.Bind(wx.EVT_BUTTON, on_currency_convert)

# Widgets participating in theme swaps
texts = [
    show1,
    show4,
    show5,
    output,
    show_weather,
    weather_output,
    show_currency,
    currency_output,
    convert,
    nowtime,
    weather_btn,
    currency_btn,
]
variables = [
    inputdt,
    fromtz,
    totz,
    convert,
    nowtime,
    weather_btn,
    currency_btn,
]

frame.Show()
app.MainLoop()


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
