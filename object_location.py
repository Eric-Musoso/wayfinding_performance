import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import LineString
import folium
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash
from datetime import timedelta
import plotly.express as px
# import matplotlib.pyplot as plt

# Step 1: Load the JSON files and extract geospatial data for both groups
file_path = r"D:\Munster\ThirdSemester\Theses\data\datan\group1.json"
with open(file_path, 'r') as file:
    data = json.load(file)

participants = data['players']
p = participants[0]
waypoints = data['waypoints']

file_path1 = r"D:\Munster\ThirdSemester\Theses\data\datan\group2.json"
with open(file_path1, 'r') as file:
    data1 = json.load(file)
# Participants
participants1 = data1['players']
p1 = participants1[0]

waypoints1 = data1['events']
waypoints1 = pd.DataFrame(waypoints1)
filtered_df = waypoints1[waypoints1['task'].apply(lambda x: isinstance(x, dict) and x.get('type') == 'theme-object')]
print(filtered_df)

filtered_df.columns = filtered_df.columns.str.strip()

# Step 1: Extract relevant information
extracted_events = []
for idx, ev in filtered_df.iterrows():
    task = ev.get('task', {})
    interaction = ev.get('interaction', {})
    
    # Ensure that answer is a dictionary before accessing 'clickPosition'
    answer = ev.get('answer', {})
    if isinstance(answer, dict):
        clickPosition = answer.get('clickPosition', None)
    else:
        clickPosition = None

    geometry_data = task.get('question', {}).get('geometry', {})
    features = geometry_data.get('features', [])
    
    for feature in features:
        geometry = feature.get('geometry', {})
        data_event = {
            'timestamp': ev.get('timestamp'),
            'panCount': interaction.get('panCount', None),
            'zoomCount': interaction.get('zoomCount', None),
            'rotation': interaction.get('rotationCount', None),
            'type': geometry.get('type', None),
            'click_latitude': clickPosition[1] if clickPosition else None,
            'click_longitude': clickPosition[0] if clickPosition else None,
            'participant': ev.get('participant', p1),
            'geometry': geometry.get('coordinates', None)
        }
        extracted_events.append(data_event)

# Convert the extracted events to a DataFrame
extracted = pd.DataFrame(extracted_events)

print(extracted)

# Step 2: Find the center for initializing the map (using the first polygon's first coordinate)
center_lat = extracted['geometry'][0][0][0][1]
center_long = extracted['geometry'][0][0][0][0]

# Initialize the map
m = folium.Map(location=[center_lat, center_long], zoom_start=15)

# Step 3: Add polygons to the map
for index, row in extracted.iterrows():
    if row['type'] == 'Polygon':
        # Extract the polygon coordinates
        polygon_coords = row['geometry'][0]  # Assuming it's a simple polygon
        
        # Create a Folium polygon
        folium.Polygon(
            locations=[(lat, lon) for lon, lat in polygon_coords],  # Reversing lon, lat to lat, lon for Folium
            color='green',  # Green color for the correct location
            fill=True,
            fill_opacity=0.4
        ).add_to(m)

    # Step 4: Add the click position as a blue marker if it exists
    if pd.notnull(row['click_latitude']) and pd.notnull(row['click_longitude']):
        folium.Marker(
            location=[row['click_latitude'], row['click_longitude']],
            icon=folium.Icon(color='blue'),
            popup=f"Click Position at {row['timestamp']}"
        ).add_to(m)

# Step 5: Save the map to an HTML file and display it
m.save('Object_Localization.html')

# Display the map in a Jupyter notebook (if applicable)
m