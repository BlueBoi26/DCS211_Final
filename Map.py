# Folium is used to generate interactive Leaflet maps in HTML
import folium

# Requests is used to download GeoJSON data from external URLs
import requests

# Used to automatically open the generated maps in a web browser
import webbrowser

# OS utilities (not heavily used, but commonly included for file handling)
import os

# JSON is used to serialize Python dictionaries into JavaScript-readable format
import json

# Built-in modules used to run a simple local HTTP server
import http.server
import socketserver

# Threading allows the web server to run without blocking the rest of the script
import threading

# Time is used for delays (e.g., waiting for the server to start)
import time

# Pandas is used to load and manipulate the census data
import pandas as pd

# GeoJSON URLs
STATES_GEOJSON_URL = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"
COUNTIES_GEOJSON_URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

# Download GeoJSON data
print("Downloading GeoJSON data...")
states_geo = requests.get(STATES_GEOJSON_URL).json()
counties_geo = requests.get(COUNTIES_GEOJSON_URL).json()

# Read the census data CSV
print("Reading census data...")
census_data = pd.read_csv('county_data.csv')

# Create a dictionary for quick lookup: FIPS code -> county data
county_data_dict = {}
for _, row in census_data.iterrows():
    # Create FIPS code by combining state and county (zero-padded to 5 digits)
    state_fips = str(row['state']).zfill(2)
    county_fips = str(row['county']).zfill(3)
    full_fips = state_fips + county_fips
    
    # Store all data for this county
    county_data_dict[full_fips] = row.to_dict()

# Get column names (excluding identifiers)
data_columns = [col for col in census_data.columns if col not in ['County Name', 'state', 'county']]

# Create a mapping of state names to their national id codes
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

# MAIN MAP — US States

def create_states_map() -> map:
    """
    Creates the map using folium
    """
    m = folium.Map(location=[39.0, -98.5], zoom_start=4, tiles="CartoDB Positron")

    # Add states GeoJSON and outline them
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

    # Add working click handler: clicking a state opens its county map
    click_script = """
    <script>
    function setupClickHandlers() {
        var foundLayer = null;
        for (var key in window) {
            if (window[key] && window[key]._leaflet_id && window[key].eachLayer) {
                foundLayer = window[key];
                break;
            }
        }
         // opens the correct state map if the statelayer is found
        if (foundLayer) {
            foundLayer.eachLayer(function (stateLayer) {
                stateLayer.on('click', function (e) {
                    var stateName = e.target.feature.properties.name;
                    var filename = 'county_map_' + stateName.replace(/ /g, '_') + '.html';
                    window.location.href = filename;
                });
            });
        } else {
            setTimeout(setupClickHandlers, 100);
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(setupClickHandlers, 500);
        });
    } else {
        setTimeout(setupClickHandlers, 500);
    }
    </script>
    """
    
    # Insert the click handler code
    m.get_root().html.add_child(folium.Element(click_script))

    return m

# COUNTY MAPS

def create_county_map(state_name, state_fips_code):
    """
    Creates a map for each state showing its counties
    
    :param state_name: The state's name
    :param state_fips_code: The state's FIPS code
    """

    # Filter counties by national id
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

    # Compute center to center the counties on the map
    # Collect all latitude/longitude pairs from every county geometry
    # This is used to compute a visual center for the state map
    all_coords = []
    for feature in state_counties['features']:
        # Extract the coordinate data for the county geometry
        coords = feature['geometry']['coordinates']

        # Handle single-polygon counties
        if feature['geometry']['type'] == 'Polygon':
            # Convert (lon, lat) to (lat, lon) for Folium
            all_coords.extend([[coord[1], coord[0]] for coord in coords[0]])
        else:
            # Handle multi-polygon counties (e.g., counties with islands)
            for polygon in coords:
                all_coords.extend([[coord[1], coord[0]] for coord in polygon[0]])


    center_lat = sum(c[0] for c in all_coords) / len(all_coords)
    center_lon = sum(c[1] for c in all_coords) / len(all_coords)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="CartoDB Positron")

    title_html = f'''
        <div style="position: fixed; top: 10px; left: 50px; width: 300px;
                    background-color: white; border:2px solid grey;
                    padding: 10px; z-index:9999; font-size:16px;">
            <b>{state_name} Counties</b><br>
            <a href="us_states_map.html" style="color: blue; text-decoration: none;">← Back to US Map</a>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Embed county data as JSON
    county_data_json = json.dumps(county_data_dict)
    data_columns_json = json.dumps(data_columns)
    
    county_geo = folium.GeoJson(
        state_counties,
        name=f"{state_name} Counties",
        style_function=lambda feature: {
            "fillColor": "#ffffff",
            "color": "#000000",
            "weight": 1,
            "fillOpacity": 0.3,
        },

        tooltip=folium.GeoJsonTooltip(
            fields=["NAME"],
            aliases=["County:"],
            localize=True,
        ),
    ).add_to(m)

    # Enhanced selection JS with full county data
    selection_js = f"""
    <script>
    
    // embedded county data
    const countyDataDict = {county_data_json};
    const dataColumns = {data_columns_json};
    
    // stores county FIPS codes
    let selectedCounties = [];

    // handles missing and large numbers
    function formatNumber(num) {{
        if (num === null || num === undefined || isNaN(num)) return 'N/A';
        if (num === -666666666) return 'N/A';  // Handle missing values
        if (Math.abs(num) >= 1000) {{
            return num.toLocaleString('en-US', {{maximumFractionDigits: 0}});
        }}
        return num.toLocaleString('en-US', {{maximumFractionDigits: 2}});
    }}

    // computes column-wise averages
    function computeAverages(dataList) {{
        if (dataList.length === 0) return {{}};

        let sums = {{}};
        let counts = {{}};

        dataList.forEach(countyFips => {{
            const countyData = countyDataDict[countyFips];
            if (!countyData) return;
            
            dataColumns.forEach(key => {{
                let val = countyData[key];
                if (typeof val === "number" && val !== -666666666 && !isNaN(val)) {{
                    if (!sums[key]) {{
                        sums[key] = 0;
                        counts[key] = 0;
                    }}
                    sums[key] += val;
                    counts[key] += 1;
                }}
            }});
        }});

        let result = {{}};
        for (let key in sums) {{
            result[key] = sums[key] / counts[key];
        }}
        return result;
    }}

    // updates county on click to re-render html box
    function updateStatsBox() {{
        let box = document.getElementById("county-stats-box");
        if (!box) return;

        if (selectedCounties.length === 0) {{
            box.innerHTML = "<b>No counties selected</b><br><small>Click on counties to view their data</small>";
            return;
        }}

        let html = `<b>Selected Counties: ${{selectedCounties.length}}</b><br>`;
        
        if (selectedCounties.length === 1) {{
            // show full data for single county
            const fips = selectedCounties[0];
            const countyData = countyDataDict[fips];
            
            if (countyData) {{
                html += `<div style="font-size: 14px; font-weight: bold; margin-top: 10px;">${{countyData['County Name']}}</div>`;
                html += '<hr style="margin: 5px 0;">';
                html += '<div style="max-height: 400px; overflow-y: auto;">';
                
                dataColumns.forEach(key => {{
                    const value = countyData[key];
                    html += `<div style="margin: 3px 0;"><b>${{key}}:</b> ${{formatNumber(value)}}</div>`;
                }});
                
                html += '</div>';
            }}
        }} else {{
            // show averages for multiple counties
            let averages = computeAverages(selectedCounties);
            html += '<small>(Showing averages)</small>';
            html += '<hr style="margin: 5px 0;">';
            html += '<div style="max-height: 400px; overflow-y: auto;">';
            
            for (let key in averages) {{
                html += `<div style="margin: 3px 0;"><b>${{key}}:</b> ${{formatNumber(averages[key])}}</div>`;
            }}
            
            html += '</div>';
        }}

        box.innerHTML = html;
    }}

    // county polygon clickhandling
    function setupCountySelection(countyLayerGroup) {{

        countyLayerGroup.eachLayer(function(layer) {{

            const originalStyle = {{
                weight: 1,
                color: "#000000",
                fillColor: "#ffffff",
                fillOpacity: 0.3
            }};

            const highlightStyle = {{
                weight: 3,
                color: "#1f78b4",
                fillColor: "#1f78b4",
                fillOpacity: 0.6
            }};

            layer.on("click", function (e) {{
                const fips = e.target.feature.id;
                const index = selectedCounties.indexOf(fips);

                if (index === -1) {{
                    selectedCounties.push(fips);
                    layer.setStyle(highlightStyle);
                }} else {{
                    selectedCounties.splice(index, 1);
                    layer.setStyle(originalStyle);
                }}

                updateStatsBox();
            }});
        }});
    }}

    document.addEventListener("DOMContentLoaded", function() {{
        setTimeout(function () {{

            if (!document.getElementById("county-stats-box")) {{
                let statsBox = document.createElement("div");
                statsBox.id = "county-stats-box";
                statsBox.style.position = "fixed";
                statsBox.style.bottom = "20px";
                statsBox.style.right = "20px";
                statsBox.style.width = "320px";
                statsBox.style.maxHeight = "500px";
                statsBox.style.overflowY = "auto";
                statsBox.style.background = "white";
                statsBox.style.border = "2px solid black";
                statsBox.style.padding = "10px";
                statsBox.style.zIndex = 9999;
                statsBox.style.fontSize = "12px";
                statsBox.innerHTML = "<b>No counties selected</b><br><small>Click on counties to view their data</small>";
                document.body.appendChild(statsBox);
            }}

            let countyLayerGroup = null;
            for (let key in window) {{
                if (
                    window[key] && 
                    window[key]._layers &&
                    Object.values(window[key]._layers)[0]?.feature?.properties?.NAME
                ) {{
                    countyLayerGroup = window[key];
                    break;
                }}
            }}

            if (countyLayerGroup) {{
                setupCountySelection(countyLayerGroup);
            }} else {{
                console.log("Could not find county GeoJSON layer.");
            }}

        }}, 500);
    }});

    </script>
    """
    m.get_root().html.add_child(folium.Element(selection_js))

    return m

# START LOCAL SERVER
def start_server(port=8000):
    """
    Starts a simple local HTTP server to serve the generated HTML map files.
    This allows the maps to be accessed in a web browser using localhost.
    """

    # Use Python's built-in request handler to serve files from the current directory
    Handler = http.server.SimpleHTTPRequestHandler

    # Allow the server to reuse the same port if it was recently closed
    socketserver.TCPServer.allow_reuse_address = True

    # Create and start the TCP server
    with socketserver.TCPServer(("", port), Handler) as httpd:
        # Print helpful instructions for the user
        print(f"\nServer running at http://localhost:{port}/")
        print(f"Opening browser to http://localhost:{port}/us_states_map.html")
        print("Press Ctrl+C to stop the server\n")

        # Keep the server running until the program is interrupted
        httpd.serve_forever()


# Create and save the main US states map
print("\nCreating US states map...")
states_map = create_states_map()
states_map.save("us_states_map.html")
print("Saved us_states_map.html")

# Generate and save a county-level map for each state
print("\nCreating county maps for each state...")
for state_name, fips_code in state_fips.items():
    # Indicate which state is currently being processed
    print(f"  Processing {state_name}...", end=" ")

    county_map = create_county_map(state_name, fips_code)

    if county_map:
        # Save the county map using a filename based on the state name
        filename = f"county_map_{state_name.replace(' ', '_')}.html"
        county_map.save(filename)
        print("O")  # Map created successfully
    else:
        print("X")  # No county data found for this state


print("\nAll maps created successfully!")
print("\nHow to use:")
print("- Click on any state to view its counties")
print("- Click on counties to view their census data")
print("- Select multiple counties to see averaged statistics")

# Start server in background thread
PORT = 8000
server_thread = threading.Thread(target=start_server, args=(PORT,), daemon=True)
server_thread.start()

# Wait a moment for server to start, then open browser
time.sleep(1)
webbrowser.open(f'http://localhost:{PORT}/us_states_map.html')

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nServer stopped.")