import streamlit as st
import pandas as pd
import folium
from folium.plugins import AntPath
from streamlit_folium import folium_static
from datetime import datetime
import pytz
import math

# -------------------------------------------------------------------------
# 1) READ CSVs WITH STREAMLIT CACHE
# -------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('flights_today_master.csv')   # Flight data (has the coordinates)
    sensornet = pd.read_csv('my_data.csv')         # Sensor data (includes 'time', 'callsign', 'type', 'distance', 'lasmax_dB', etc.)
    return df, sensornet

# Load data
df, sensornet = load_data()

# Schiphol coordinates
SCHIPHOL_LAT = 52.3105
SCHIPHOL_LON = 4.7683

# -------------------------------------------------------------------------
# 2) PARSE & TIMEZONE NORMALIZE
#    (Keep only the "HH:MM:SS" portion in each dataset, both in UTC.)
# -------------------------------------------------------------------------
def parse_time_ignoring_weekday(t_str):
    """
    Removes something like 'Mon' (the first 4 chars) and attempts
    to parse what's left as '%I:%M:%S %p'. If parsing fails, returns None.
    """
    if not isinstance(t_str, str):
        return None
    time_part = t_str[4:].strip()  # remove something like "Mon "
    try:
        return pd.to_datetime(time_part, format="%I:%M:%S %p", errors='coerce')
    except:
        return None

# --------------------- Flight data times => final in UTC HH:MM:SS ---------------------
df['Time'] = df['Time'].apply(parse_time_ignoring_weekday)
df['Time'] = df['Time'].dt.tz_localize('Etc/GMT+3').dt.tz_convert('UTC')
df['Time'] = df['Time'].dt.strftime('%H:%M:%S')  # Now just HH:MM:SS as a string

# --------------------- Sensor data => final in UTC HH:MM:SS ---------------------
sensornet['time'] = pd.to_datetime(sensornet['time'], errors='coerce')
sensornet['time'] = sensornet['time'].dt.tz_localize('Europe/Amsterdam').dt.tz_convert('UTC')
sensornet['time'] = sensornet['time'].dt.strftime('%H:%M:%S')

# -------------------------------------------------------------------------
# 3) HELPER FUNCTIONS
# -------------------------------------------------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    from math import radians, sin, cos, atan2, sqrt
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(d_lon/2)**2
    c = 2*atan2(sqrt(a), sqrt(1-a))
    return R * c

def compute_bearing(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, atan2, degrees
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(d_lon)
    brng = math.atan2(x, y)
    brng = degrees(brng)
    return (brng + 360) % 360

def midpoint(lat1, lon1, lat2, lon2):
    return ((lat1 + lat2) / 2.0, (lon1 + lon2) / 2.0)

def time_str_to_seconds(t_str):
    """
    Given a time string in HH:MM:SS format, convert to total seconds from midnight.
    Example: "01:02:03" -> 3723 seconds.
    """
    if not isinstance(t_str, str) or len(t_str.split(':')) != 3:
        return None
    hh, mm, ss = t_str.split(':')
    return int(hh)*3600 + int(mm)*60 + int(ss)

# -------------------------------------------------------------------------
# 4) PLOT THE FLIGHT PATH + DOT MARKERS (with altitude in popup)
# -------------------------------------------------------------------------
def plot_flight(df, flight_number, map_obj, color):
    """
    Expects 'df' to have a 'Time' column containing only HH:MM:SS strings in UTC.
    """
    flight_df = df[df['FlightNumber'] == flight_number].copy()
    flight_df.sort_values(by='Time', inplace=True, na_position='first')
    
    # Keep only points within 20 km of Schiphol
    def distance_to_schiphol(row):
        return haversine_distance(SCHIPHOL_LAT, SCHIPHOL_LON, row['Latitude'], row['Longitude'])
    
    flight_df['DistanceToSchiphol'] = flight_df.apply(distance_to_schiphol, axis=1)
    flight_df = flight_df[flight_df['DistanceToSchiphol'] < 20]
    
    if len(flight_df) < 2:
        return  # No path to draw if fewer than 2 points
    
    coords = flight_df[['Latitude','Longitude']].values.tolist()

    # Use AntPath with slower animation (delay set to 2500ms)
    folium.plugins.AntPath(
        coords, color=color, weight=3, opacity=0.6, delay=2500
    ).add_to(map_obj)
    
    # For each segment along the flight path, place a small dot marker (in matching color)
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        row2 = flight_df.iloc[i + 1]
        
        time2 = row2.get('Time', None)
        altitude_ft = row2.get('Altitude_feet', 'N/A')
        
        if not time2 or time2 in ["NaT", "nan"]:
            popup_str = (
                f"<b>Flight:</b> {flight_number}<br>"
                f"<b>Time:</b> N/A<br>"
                f"<b>Altitude:</b> {altitude_ft} ft"
            )
        else:
            popup_str = (
                f"<b>Flight:</b> {flight_number}<br>"
                f"<b>Time:</b> {time2} UTC<br>"
                f"<b>Altitude:</b> {altitude_ft} ft"
            )
        
        lat_mid, lon_mid = midpoint(lat1, lon1, lat2, lon2)
        
        folium.CircleMarker(
            location=[lat_mid, lon_mid],
            radius=3,  # small dot marker
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup_str
        ).add_to(map_obj)

# -------------------------------------------------------------------------
# 5) BUILD THE BASE MAP
# -------------------------------------------------------------------------
def create_map():
    m = folium.Map(location=[52.235, 4.748], zoom_start=11.5)

    # 20 km circle around Schiphol
    folium.Circle(
        location=[SCHIPHOL_LAT, SCHIPHOL_LON],
        radius=20000,
        color='lightgray',
        fill=True,
        fill_color='black',
        fill_opacity=0
    ).add_to(m)
    
    return m

# -------------------------------------------------------------------------
# 6) ADD FLIGHT AND SENSOR MARKERS
# -------------------------------------------------------------------------
def add_flights_and_sensors(m, flight_numbers, colors):
    # Plot flight paths
    for fn, col in zip(flight_numbers, colors):
        sub_df = df[df['FlightNumber'] == fn].copy()
        plot_flight(sub_df, fn, m, col)
    
    # Add stationary sensors
    sensors = [
        ("Kudelstaartseweg", 52.235, 4.748)
    ]

    for i, (name, lat, lon) in enumerate(sensors):
        # For Kudelstaartseweg, use the PNG marker
        if name == "Kudelstaartseweg":
            folium.Marker(
                location=[lat, lon],
                icon=folium.CustomIcon(
                    icon_image='/path/to/your/sound-sensor2.png',  # Update this path
                    icon_size=(50, 50)
                ),
                popup=f"Sensor: {name}"
            ).add_to(m)
        else:
            color = "darkorange"
            marker_html = f"""
            <div style="border-radius: 50%; background-color: {color};
                        width: 30px; height: 30px;
                        display: flex; align-items: center; justify-content: center;">
                <span style="font-weight: bold; color: black;">{name[:2]}</span>
            </div>
            """
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    icon_size=(30,30),
                    icon_anchor=(15,15),
                    html=marker_html
                ),
                popup=f"Sensor: {name}"
            ).add_to(m)

# -------------------------------------------------------------------------
# 7) DISPLAY THE MAP IN STREAMLIT
# -------------------------------------------------------------------------
def display_map():
    m = create_map()
    
    flight_numbers = ["KLM1342", "PGT1259"]
    colors = ["blue", "red"]
    
    add_flights_and_sensors(m, flight_numbers, colors)
    
    folium_static(m)

# Display the map in Streamlit
if __name__ == "__main__":
    display_map()
