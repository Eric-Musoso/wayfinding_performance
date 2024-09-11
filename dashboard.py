import json
import geopandas as gpd
from shapely.geometry import Point
import folium
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# Step 1: Load the JSON file and extract geospatial data for group 1
file_path = r"D:\Munster\ThirdSemester\Theses\data\datan\group1.json"
with open(file_path, 'r') as file:
    data = json.load(file)

participants = data['players']
p = participants[0]
waypoints = data['waypoints']

file_path1 = r"D:\Munster\ThirdSemester\Theses\data\datan\group2.json"
with open(file_path1, 'r') as file:
    data1 = json.load(file)

participants1 = data1['players']
p1 = participants1[0]
waypoints1 = data1['waypoints']

# Step 2: Extract necessary information and create a GeoDataFrame
extracted_data = []
for wp in waypoints:
    position = wp.get('position', {})
    coords = position.get('coords', {})
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
        'rotation': interaction.get('rotation'),
        'participant': wp.get('participant', p)
    }
    extracted_data.append(data_entry)

# Step 2: Extract necessary information for group 2
extracted_data1 = []
for wp1 in waypoints1:
    position1 = wp1.get('position', {})
    coords1 = position1.get('coords', {})
    interaction1 = wp1.get('interaction', {})

    data_entry1 = {
        'timestamp': wp1.get('timestamp'),
        'latitude': coords1.get('latitude'),
        'longitude': coords1.get('longitude'),
        'altitude': coords1.get('altitude'),
        'speed': coords1.get('speed'),
        'heading': coords1.get('heading'),
        'accuracy': coords1.get('accuracy'),
        'taskNo': wp1.get('taskNo'),
        'taskCategory': wp1.get('taskCategory'),
        'panCount': interaction1.get('panCount'),
        'zoomCount': interaction1.get('zoomCount'),
        'rotation': interaction1.get('rotation'),
        'participant': wp1.get('participant', p1)
    }
    extracted_data1.append(data_entry1)

# Combine both datasets
alldata = extracted_data + extracted_data1  # concatenate lists

# Check unique participants
participants_set = set([d['participant'] for d in alldata])  # use set to get unique participants
print(participants_set)

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    alldata,
    geometry=[Point(data['longitude'], data['latitude']) for data in alldata],
    crs="EPSG:4326"  # WGS84 Latitude/Longitude
)

# Filter the tasks for navigation
nav_tasks = gdf[(gdf['taskCategory'] == 'nav') & (gdf['taskNo'] == 1)]
print(nav_tasks)

# Step 3: Create a function to generate the map
def create_map(nav_tasks, opacity):
    map_center = [nav_tasks.geometry.y.mean(), nav_tasks.geometry.x.mean()]
    m = folium.Map(location=map_center, zoom_start=14)

    # Color based on heading
    def get_color(heading):
        if heading < 90:
            return 'red'
        elif heading < 180:
            return 'orange'
        elif heading < 270:
            return 'yellow'
        else:
            return 'blue'

    for _, row in nav_tasks.iterrows():
        folium.CircleMarker(
            location=(row.geometry.y, row.geometry.x),
            radius=5,
            color=get_color(row.heading),
            fill=True,
            fill_color=get_color(row.heading),
            fill_opacity=opacity
        ).add_to(m)

    map_path = "map.html"
    m.save(map_path)
    return map_path

# Generate the map initially with default values (first participant and default opacity)
default_participant = nav_tasks['participant'].unique()[0]
initial_map_path = create_map(nav_tasks[nav_tasks['participant'] == default_participant], 0.5)

# Step 4: Set up Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Label("Select Task Participant:"),
            dcc.Dropdown(
                id='task-participant-dropdown',
                options=[{'label': participant, 'value': participant} for participant in nav_tasks['participant'].unique()],
                value=default_participant  # Default selection
            )
        ], width=4),

        dbc.Col([
            html.Label("Map Opacity:"),
            dcc.Slider(
                id='opacity-slider',
                min=0,
                max=1,
                step=0.1,
                value=0.5,  # Default opacity
                marks={0: '0', 1: '1'}
            )
        ], width=4)
    ]),

    dbc.Row([
        dbc.Col(
            html.Iframe(id="map", srcDoc=open(initial_map_path, "r").read(), width="50%", height="400")
        )
    ])
])

# Step 5: Define app callback for map updates
@app.callback(
    Output('map', 'srcDoc'),
    [Input('task-participant-dropdown', 'value'),
     Input('opacity-slider', 'value')]
)
def update_map(selected_participant, opacity):
    filtered_data = nav_tasks[nav_tasks['participant'] == selected_participant]
    map_path = create_map(filtered_data, opacity)
    return open(map_path, 'r').read()

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
