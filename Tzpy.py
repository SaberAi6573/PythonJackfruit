from datetime import datetime , time
import pytz
import wx
from tzlocal import get_localzone_name
import weather_api as wa

result = ""
text_widgets = []
input_widgets = []

def time_zone_converter(time_str, from_tz, to_tz, time_format="%Y-%m-%d %H:%M:%S"):
    """
    Convert time between time zones using pytz
    """
    # Create timezone objects
    from_timezone = pytz.timezone(from_tz)
    to_timezone = pytz.timezone(to_tz)
    
    # Parse the input time (naive datetime)
    naive_time = datetime.strptime(time_str, time_format)
    
    # Localize to source timezone (handles DST properly)
    localized_time = from_timezone.localize(naive_time)
    
    # Convert to target timezone
    converted_time = localized_time.astimezone(to_timezone)
    
    return converted_time.strftime(time_format)

def back_fore_ground(bg_color, text_mode):
    panel.SetBackgroundColour(bg_color)
    if text_mode == "light":
        text_color = wx.Colour(245, 245, 245)
        item_text = wx.Colour(25, 25, 25)
        item_bg = wx.Colour(250, 250, 250)
    else:
        text_color = wx.Colour(32, 32, 32)
        item_text = wx.Colour(25, 25, 25)
        item_bg = wx.Colour(255, 255, 255)

    for text in texts:
        text.SetForegroundColour(text_color)

    for item in variables:
        item.SetForegroundColour(item_text)
        item.SetBackgroundColour(item_bg)

    panel.Refresh()


def time_background_converter_output():
    if not result:
        return
    try:
        time_result = datetime.strptime(result, "%Y-%m-%d %H:%M:%S").time()
    except ValueError:
        return

    if time(0,0,0)<= time_result < time(4,0,0):
        back_fore_ground(wx.Colour(6, 10, 28), "light")
    elif time(4,0,0)<= time_result < time(6,0,0):
        back_fore_ground(wx.Colour(28, 45, 85), "light")
    elif time(6,0,0)<= time_result < time(8,0,0):
        back_fore_ground(wx.Colour(250, 189, 120), "dark")
    elif time(8,0,0)<= time_result < time(10,0,0):
        back_fore_ground(wx.Colour(255, 209, 145), "dark")
    elif time(10,0,0)<= time_result < time(12,0,0):
        back_fore_ground(wx.Colour(255, 234, 185), "dark")
    elif time(12,0,0)<= time_result < time(15,0,0):
        back_fore_ground(wx.Colour(240, 244, 220), "dark")
    elif time(15,0,0)<= time_result < time(17,0,0):
        back_fore_ground(wx.Colour(248, 196, 130), "dark")
    elif time(17,0,0)<= time_result < time(19,0,0):
        back_fore_ground(wx.Colour(252, 140, 90), "dark")
    elif time(19,0,0)<= time_result < time(22,0,0):
        back_fore_ground(wx.Colour(54, 34, 70), "light")
    else:
        back_fore_ground(wx.Colour(8, 6, 26), "light")

def time_background_converter_input():
    try:
        time_input = datetime.strptime(inputdt.GetValue(), "%Y-%m-%d %H:%M:%S").time()
    except ValueError:
        return

    if time(0,0,0)<= time_input < time(4,0,0):
        back_fore_ground(wx.Colour(6, 10, 28), "light")
    elif time(4,0,0)<= time_input < time(6,0,0):
        back_fore_ground(wx.Colour(28, 45, 85), "light")
    elif time(6,0,0)<= time_input < time(8,0,0):
        back_fore_ground(wx.Colour(250, 189, 120), "dark")
    elif time(8,0,0)<= time_input < time(10,0,0):
        back_fore_ground(wx.Colour(255, 209, 145), "dark")
    elif time(10,0,0)<= time_input < time(12,0,0):
        back_fore_ground(wx.Colour(255, 234, 185), "dark")
    elif time(12,0,0)<= time_input < time(15,0,0):
        back_fore_ground(wx.Colour(240, 244, 220), "dark")
    elif time(15,0,0)<= time_input < time(17,0,0):
        back_fore_ground(wx.Colour(248, 196, 130), "dark")
    elif time(17,0,0)<= time_input < time(19,0,0):
        back_fore_ground(wx.Colour(252, 140, 90), "dark")
    elif time(19,0,0)<= time_input < time(22,0,0):
        back_fore_ground(wx.Colour(54, 34, 70), "light")
    else:
        back_fore_ground(wx.Colour(8, 6, 26), "light")


def on_now(event):
    now=datetime.now()
    inputdt.SetValue(now.strftime("%Y-%m-%d %H:%M:%S"))
    fromtz.SetStringSelection(get_localzone_name())
    time_background_converter_input()
    


def simple_frame():
    global time_str,from_tz,to_tz
    time_str=inputdt.GetValue()
    time_background_converter_input()
    from_tz=fromtz.GetStringSelection()
    to_tz=totz.GetStringSelection()
    
def on_weather(event):
    """
    Weather at datetime in inputdt and timezone selected in totz (target TZ).
    """
    dt_str_local = inputdt.GetValue().strip()
    if not dt_str_local:
        weather_output.SetLabel("Error: Enter datetime (YYYY-MM-DD HH:MM:SS)")
        return

    tz_name = totz.GetStringSelection()
    if not tz_name:
        weather_output.SetLabel("Error: Select a target timezone (To TZ) for weather.")
        return

    # Validate datetime string
    try:
        datetime.strptime(dt_str_local, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        weather_output.SetLabel("Error: Invalid datetime format.")
        return

    try:
        weather = wa.get_weather_for_datetime(dt_str_local, tz_name)
        display_time = weather["time"].replace("T", " ")
        msg = (
            f"🌤 {weather['city']}, {weather['country']} @ {display_time}\n"
            f"🌡 Temp: {weather['temperature']}°C   "
            f"💧 Humidity: {weather['humidity']}%   "
            f"🌧 Precip: {weather['precipitation']} mm"
        )
        weather_output.SetLabel(msg)
    except Exception as e:
        weather_output.SetLabel(f"Weather error: {e}")

    
def on_convert(event):
    simple_frame()
    global result

    try:
        result=time_zone_converter(time_str,from_tz,to_tz)
        output.SetLabel(f'📍 {from_tz} : {time_str}  ->  🎯 {to_tz} : {result}')
        time_background_converter_output()
    except Exception:
        output.SetLabel(f"Error: Invalid input or timezone")

    
        
# ---------------- UI SETUP (wxPython) ---------------- #

timezones = pytz.all_timezones
app = wx.App(False)
frame = wx.Frame(
    None,
    title="Time Zone & Weather Viewer",
    size=(700, 550),
    style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
)
panel = wx.Panel(frame, style=wx.SIMPLE_BORDER)

show1 = wx.StaticText(panel, label="ENTER DATE & TIME", pos=(220, 55))
inputdt = wx.TextCtrl(panel, pos=(200, 85), size=(250, 25), style=wx.SIMPLE_BORDER)
inputdt.SetHint("YYYY-MM-DD HH:MM:SS e.g. 2025-12-05 14:30:00")

nowtime = wx.Button(panel, label="CURRENT LOCAL", pos=(270, 120), size=(120, 30), style=wx.BORDER_RAISED)

show4 = wx.StaticText(panel, label="Select Source and Target Timezones", pos=(220, 170))
fromtz = wx.Choice(panel, choices=timezones, pos=(200, 200), size=(250, 30), style=wx.BORDER_SUNKEN)
totz = wx.Choice(panel, choices=timezones, pos=(200, 240), size=(250, 30), style=wx.BORDER_SUNKEN)

convert = wx.Button(panel, label="CONVERT TIME", pos=(270, 280), size=(120, 30), style=wx.BORDER_RAISED)
show5 = wx.StaticText(panel, label="CONVERTED TIME WILL APPEAR HERE ↓", pos=(200, 320), style=wx.SIMPLE_BORDER)
output = wx.StaticText(panel, label="", pos=(50, 350), size=(600, 30), style=wx.SIMPLE_BORDER)

# Weather UI
show_weather = wx.StaticText(panel, label="WEATHER (Uses target timezone city)", pos=(220, 390))
weather_btn = wx.Button(panel, label="GET WEATHER", pos=(270, 420), size=(120, 30), style=wx.BORDER_RAISED)
weather_output = wx.StaticText(panel, label="", pos=(50, 460), size=(600, 60), style=wx.SIMPLE_BORDER)

# Bindings
inputdt.Bind(wx.EVT_TEXT, simple_frame)
fromtz.Bind(wx.EVT_CHOICE, simple_frame)
totz.Bind(wx.EVT_CHOICE, simple_frame)
convert.Bind(wx.EVT_BUTTON, on_convert)
nowtime.Bind(wx.EVT_BUTTON, on_now)
weather_btn.Bind(wx.EVT_BUTTON, on_weather)

# Important: include all texts & interactive widgets
texts = [
    show1, show4, show5, output,
    show_weather, weather_output,
    convert, nowtime, weather_btn
]
variables = [
    inputdt, fromtz, totz,
    convert, nowtime, weather_btn
]

frame.Show()
app.MainLoop()


# # Simple user input
# print("=== pytz Time Zone Converter ===")
# print("Example: 2024-01-15 14:30:00")

# time_str = input("Enter time (YYYY-MM-DD HH:MM:SS): ")
# from_tz = input("Enter source timezone (e.g., US/Eastern): ")
# to_tz = input("Enter target timezone (e.g., Asia/Tokyo): ")

# result = time_zone_converter(time_str, from_tz, to_tz)

# print(f"\n🔄 Conversion Result:")
# print(f"📍 {from_tz}: {time_str}")
# print(f"🎯 {to_tz}: {result}")
