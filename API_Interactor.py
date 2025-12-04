import folium
import requests
import webbrowser
import os
import json
import http.server
import socketserver
import threading

# GeoJSON URLs
STATES_GEOJSON_URL = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"
COUNTIES_GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

# Download GeoJSON
print("Downloading GeoJSON data...")
states_geo = requests.get(STATES_GEOJSON_URL).json()
counties_geo = requests.get(COUNTIES_GEOJSON_URL).json()

# Create a mapping of state names to their FIPS codes
state_fips = {
    'Alabama': '01', 'Alaska': '02', 'Arizona': '04', 'Arkansas': '05',
    'California': '06', 'Colorado': '08', 'Connecticut': '09', 'Delaware': '10',
    'Florida': '12', 'Georgia': '13', 'Hawaii': '15', 'Idaho': '16',
    'Illinois': '17', 'Indiana': '18', 'Iowa': '19', 'Kansas': '20',
    'Kentucky': '21', 'Louisiana': '22', 'Maine': '23', 'Maryland': '24',
    'Massachusetts': '25', 'Michigan': '26', 'Minnesota': '27', 'Mississippi': '28',
    'Missouri': '29', 'Montana': '30', 'Nebraska': '31', 'Nevada': '32',
    'New Hampshire': '33', 'New Jersey': '34', 'New Mexico': '35', 'New York': '36',
    'North Carolina': '37', 'North Dakota': '38', 'Ohio': '39', 'Oklahoma': '40',
    'Oregon': '41', 'Pennsylvania': '42', 'Rhode Island': '44', 'South Carolina': '45',
    'South Dakota': '46', 'Tennessee': '47', 'Texas': '48', 'Utah': '49',
    'Vermont': '50', 'Virginia': '51', 'Washington': '53', 'West Virginia': '54',
    'Wisconsin': '55', 'Wyoming': '56', 'District of Columbia': '11'
}

# -------------------------------------------------------------
# MAIN MAP – US STATES
# -------------------------------------------------------------

def create_states_map():
    m = folium.Map(location=[39.0, -98.5], zoom_start=4, tiles="CartoDB Positron")

    # Add states GeoJSON
    geojson = folium.GeoJson(
        states_geo,
        name="US States",
        style_function=lambda feature: {
            "fillColor": "#ffffff",
            "color": "#000000",
            "weight": 1,
            "fillOpacity": 0.1,
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "#1f78b4",
            "fillOpacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name"],
            aliases=["State:"],
            localize=True,
        ),
    ).add_to(m)

    # Add working click handler - attach directly to the geojson object
    click_script = """
    <script>
    function setupClickHandlers() {
        // Find the GeoJSON layer by iterating through map layers
        var foundLayer = null;
        
        // Try to find the layer in the window object
        for (var key in window) {
            if (window[key] && window[key]._leaflet_id && window[key].eachLayer) {
                foundLayer = window[key];
                break;
            }
        }
        
        if (foundLayer) {
            foundLayer.eachLayer(function (stateLayer) {
                stateLayer.on('click', function (e) {
                    var stateName = e.target.feature.properties.name;
                    var filename = 'county_map_' + stateName.replace(/ /g, '_') + '.html';
                    console.log('Navigating to: ' + filename);
                    window.location.href = filename;
                });
            });
            console.log('Click handlers attached successfully');
        } else {
            console.log('Layer not found, retrying...');
            setTimeout(setupClickHandlers, 100);
        }
    }
    
    // Wait for map to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(setupClickHandlers, 500);
        });
    } else {
        setTimeout(setupClickHandlers, 500);
    }
    </script>
    """
    m.get_root().html.add_child(folium.Element(click_script))

    return m

# -------------------------------------------------------------
# COUNTY MAPS
# -------------------------------------------------------------

def create_county_map(state_name, state_fips_code):
    # Filter counties by FIPS
    state_counties = {
        'type': 'FeatureCollection',
        'features': [
            feature for feature in counties_geo['features']
            if feature['id'].startswith(state_fips_code)
        ]
    }

    if not state_counties['features']:
        print(f"  Warning: No counties found for {state_name}")
        return None

    # Compute center
    all_coords = []
    for feature in state_counties['features']:
        coords = feature['geometry']['coordinates']
        if feature['geometry']['type'] == 'Polygon':
            all_coords.extend([[coord[1], coord[0]] for coord in coords[0]])
        else:
            for polygon in coords:
                all_coords.extend([[coord[1], coord[0]] for coord in polygon[0]])

    center_lat = sum(c[0] for c in all_coords) / len(all_coords)
    center_lon = sum(c[1] for c in all_coords) / len(all_coords)

    # Create county map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="CartoDB Positron")

    # Title + Back button
    title_html = f'''
        <div style="position: fixed; top: 10px; left: 50px; width: 300px; 
                    background-color: white; border:2px solid grey; 
                    padding: 10px; z-index:9999; font-size:16px;">
            <b>{state_name} Counties</b><br>
            <a href="us_states_map.html" style="color: blue; text-decoration: none;">← Back to US Map</a>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add county borders
    folium.GeoJson(
        state_counties,
        name=f"{state_name} Counties",
        style_function=lambda feature: {
            "fillColor": "#ffff00",
            "color": "#000000",
            "weight": 1,
            "fillOpacity": 0.3,
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "#1f78b4",
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NAME"],
            aliases=["County:"],
            localize=True,
        ),
    ).add_to(m)

    return m

# -------------------------------------------------------------
# START LOCAL SERVER
# -------------------------------------------------------------

def start_server(port=8000):
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"\n🌐 Server running at http://localhost:{port}/")
        print(f"Opening browser to http://localhost:{port}/us_states_map.html")
        print("Press Ctrl+C to stop the server\n")
        httpd.serve_forever()

# -------------------------------------------------------------
# GENERATE FILES
# -------------------------------------------------------------

print("\nCreating US states map...")
states_map = create_states_map()
states_map.save("us_states_map.html")
print("✓ Saved us_states_map.html")

print("\nCreating county maps for each state...")
for state_name, fips_code in state_fips.items():
    print(f"  Processing {state_name}...", end=" ")
    county_map = create_county_map(state_name, fips_code)
    if county_map:
        filename = f"county_map_{state_name.replace(' ', '_')}.html"
        county_map.save(filename)
        print("✓")
    else:
        print("✗")

print("\n✓ All maps created successfully!")

# Start server in background thread
PORT = 8000
server_thread = threading.Thread(target=start_server, args=(PORT,), daemon=True)
server_thread.start()

# Wait a moment for server to start, then open browser
import time
time.sleep(1)
webbrowser.open(f'http://localhost:{PORT}/us_states_map.html')

# Keep script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nServer stopped.")