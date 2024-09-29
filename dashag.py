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

participants1 = data1['players']
p1 = participants1[0]
waypoints1 = data1['waypoints']

# Step 2: Extract necessary information and create a GeoDataFrame for both groups
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

# Extract data for group 2
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
alldata = extracted_data + extracted_data1

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    alldata,
    geometry=[Point(data['longitude'], data['latitude']) for data in alldata],
    crs="EPSG:4326"  # WGS84 Latitude/Longitude
)

# Filter the tasks for navigation (safe copy with .loc[])
nav_tasks = gdf.loc[(gdf['taskCategory'] == 'theme') & (gdf['taskNo'] == 5)].copy()
print(nav_tasks)
# Convert 'timestamp' column to datetime safely
nav_tasks['timestamp'] = pd.to_datetime(nav_tasks['timestamp'])
# Group by 'participant' and calculate 'duration' and 'route length'

df_duration = nav_tasks.groupby('participant').agg(
    Duration=pd.NamedAgg(column='timestamp', aggfunc=lambda x: x.max() - x.min()),  # Calculate duration
).reset_index()

lines = (
    nav_tasks.groupby('participant')
    .apply(lambda x: LineString(x.sort_values('timestamp')[['longitude', 'latitude']].values))
    .reset_index()
)

gdf_lines = gpd.GeoDataFrame(
    lines, 
    geometry=lines[0],  # The LineString geometries created in the lambda function
    crs="EPSG:4326"
)
gdf_lines.drop(columns=0, inplace=True)

gdf_lines_projected = gdf_lines.to_crs(epsg=3395)
gdf_lines_projected['Route_length'] = gdf_lines_projected.length / 1000
gdf_lines_with_length = gdf_lines_projected.to_crs(epsg=4326)
gdf1_length = pd.merge(gdf_lines_with_length, df_duration, on='participant')
df_length = pd.DataFrame(gdf1_length.drop(columns='geometry'))
## print(df_length)

# Step 3: Create a function to generate the map
def create_map(nav_tasks, opacity=0.5, basemap="OpenStreetMap"):
    map_center = [nav_tasks.geometry.y.mean(), nav_tasks.geometry.x.mean()]
    m = folium.Map(location=map_center, zoom_start=14, tiles=basemap)
    
    # Add tile layers for switching basemaps
    folium.TileLayer('OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB positron').add_to(m)
    folium.TileLayer('CartoDB dark_matter').add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri — Source: Esri, DeLorme, NAVTEQ",
        name='Imagery'
    ).add_to(m)
    folium.LayerControl().add_to(m)  # Enable layer control
    
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

    # Add legend for heading colors
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 150px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; padding: 10px;">
    <b>Heading Legend</b><br>
    <i style="background:red;width:20px;height:20px;float:left;margin-right:8px"></i> 0-90°<br>
    <i style="background:orange;width:20px;height:20px;float:left;margin-right:8px"></i> 90-180°<br>
    <i style="background:yellow;width:20px;height:20px;float:left;margin-right:8px"></i> 180-270°<br>
    <i style="background:blue;width:20px;height:20px;float:left;margin-right:8px"></i> 270-360°
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    map_path = "map.html"
    m.save(map_path)
    return map_path

# Generate the map initially with default values (first participant, default opacity, default basemap)
default_participant = nav_tasks['participant'].unique()[0]
initial_map_path = create_map(nav_tasks[nav_tasks['participant'] == default_participant])

# Step 4: Set up Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Wayfinding Performance among Different Users", style={'text-align': 'center', 'color': 'white'})
        ])
    ], style={'background-color': 'black'}),

    dbc.Row([
        dbc.Col([
            html.Label("Select Task Participant:", style={'color': 'white'}),
            dcc.Dropdown(
                id='task-participant-dropdown',
                options=[{'label': Participant, 'value': Participant} for Participant in nav_tasks['participant'].unique()],
                value=default_participant  # Default participant selection
            )
        ], width=4)
    ]),

    dbc.Row([
        # Left Column (Map)
        dbc.Col(
            html.Iframe(id="map", srcDoc=open(initial_map_path, "r").read(), width="100%", height="500"),
            width=6  
        ),
        
        # Right Column (Data and Graph)
        dbc.Col([
            html.Div(children='Route Length(Km) Vs Time(DD/HH/MM/SS)', style={'text-align': 'center', 'color': 'white'}),
            html.Hr(),
            dcc.RadioItems(options=['Route_length', 'Duration'], value='Route_length', id='controls-and-radio-item', style={'color': 'white'}),
            dash_table.DataTable(data=df_length.to_dict('records'), page_size=6, style_table={'height': '100px', 'overflowY': 'auto'}),
            dcc.Graph(figure={}, id='controls-and-graph')
        ], width=6)  
    ])
], fluid=True, style={'background-color': 'black'})

# Step 5: Define app callback for map updates
@app.callback(
    [Output('map', 'srcDoc'),
     Output('controls-and-graph', 'figure')],
    [Input('task-participant-dropdown', 'value'),
     Input('controls-and-radio-item', 'value')]
)
def update_map(selected_participant, col_chosen):
    # Update map based on the selected participant
    filtered_data = nav_tasks[nav_tasks['participant'] == selected_participant]
    default_opacity = 0.5  # Set default opacity
    default_basemap = 'OpenStreetMap'  # Default basemap
    map_path = create_map(filtered_data, default_opacity, default_basemap)

    # Update graph based on selected radio button choice
    fig = px.histogram(df_length, x='participant', y=col_chosen)

    return open(map_path, 'r').read(), fig

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
