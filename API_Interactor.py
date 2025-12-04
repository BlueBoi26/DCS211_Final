import folium
import requests
import webbrowser
import os

# GeoJSON of US states
GEOJSON_URL = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"

# Download GeoJSON
states_geo = requests.get(GEOJSON_URL).json()

# Create map
m = folium.Map(location=[39.0, -98.5], zoom_start=4, tiles="CartoDB Positron")

folium.GeoJson(
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
    popup=folium.GeoJsonPopup(
        fields=["name"],
        labels=True,
        localize=True,
    ),
).add_to(m)

m.save("us_states_map.html")

# Open in new window
file_path = "file://" + os.path.realpath("us_states_map.html")
webbrowser.open_new(file_path)

print("Opened map in a new browser window.")
