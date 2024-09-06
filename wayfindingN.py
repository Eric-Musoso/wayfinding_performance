import json
import geopandas as gpd
from shapely.geometry import Point
import folium

# Step 1: Load the JSON file
file_path = r"D:\Munster\ThirdSemester\Theses\data\datan\datatest.json"
with open(file_path, 'r') as file:
    data = json.load(file)
print(data.keys())
# Step 2: Extract geospatial data from the 'waypoints' key
waypoints = data['waypoints']
print(waypoints)

extracted_data = []

for wp in waypoints:
    # Extracting necessary information
    position = wp.get('position', {})
    coords = position.get('coords', {})
    mapViewport = wp.get('mapViewport', {})
    interaction = wp.get('interaction', {})

    data_entry = {
        'timestamp': wp.get('timestamp'),
        'latitude': coords.get('latitude'),
        'longitude': coords.get('longitude'),
        'altitude': coords.get('altitude'),
        'speed': coords.get('speed'),
        'heading': coords.get('heading'),
        'accuracy': coords.get('accuracy'),
        'taskNo': wp.get('taskNo'),
        'taskCategory': wp.get('taskCategory'),
        'panCount': interaction.get('panCount'),
        'zoomCount': interaction.get('zoomCount'),
        'rotation': interaction.get('rotation')
    }

    extracted_data.append(data_entry)

# Step 2: Convert to a GeoDataFrame
gdf = gpd.GeoDataFrame(
    extracted_data,
    geometry=[Point(data['longitude'], data['latitude']) for data in extracted_data],
    crs="EPSG:4326"  # Assuming WGS84 Latitude/Longitude
)

# Step 3: Display the GeoDataFrame
print(gdf.head())

# Filter and display unique task categories
unique_task_categories = gdf['taskCategory'].unique()
print("Unique task categories:", unique_task_categories)

# Count occurrences of each task category
task_category_counts = gdf['taskCategory'].value_counts()
print("\nTask category counts:\n", task_category_counts)

# Filter GeoDataFrame to only include 'nav' taskCategory
nav_tasks = gdf[(gdf['taskCategory'] == 'nav') & (gdf['taskNo'] == 1)]
print(nav_tasks.head())

# You can also check how many entries belong to this category
print(f"Number of 'nav' tasks: {len(nav_tasks)}")

map_center = [nav_tasks.geometry.y.mean(), nav_tasks.geometry.x.mean()]
m = folium.Map(location=map_center, zoom_start=18)
for _, row in nav_tasks.iterrows():
    folium.CircleMarker(
        location=(row.geometry.y, row.geometry.x),  # Extract latitude and longitude from geometry
        radius=2,  # Small radius for markers
        color='blue',  # Marker outline color
        fill=True,  # Enable filling the marker
        fill_color='blue',  # Fill color
        fill_opacity=0.7  # Slight transparency
    ).add_to(m)

m.save('map.html')
