import sys
import json
import folium


# Example: load dataset (placeholder)
# df = pd.read_csv('utilities.csv') # columns: ['lat','lon','state','county','utility_value']


# Create base map
m = folium.Map(location=[39.5, -98.35], zoom_start=5)


# --- Hover Tooltip for Average by State (example) ---
# Compute state averages
def create_state_hover_layer(df):
    state_avg = df.groupby('state')['utility_value'].mean().reset_index()
    for _, row in state_avg.iterrows():
        folium.CircleMarker(
            location=[df[df['state']==row['state']]['lat'].mean(),
            df[df['state']==row['state']]['lon'].mean()],
            radius=5,
            fill=True,
            tooltip=f"{row['state']} avg: {row['utility_value']:.2f}"
        ).add_to(m)


# --- Circle Draw + Average Computation ---
from folium.plugins import Draw


draw = Draw(
    draw_options={"circle": True, "rectangle": False, "polygon": False},
    edit_options={"edit": True}
)
draw.add_to(m)


# Placeholder JS callback for computing average inside circle
circle_avg_js = """
function computeAverage(e) {
    var layer = e.layer;
    var center = layer.getLatLng();
    var radius = layer.getRadius();


    // Placeholder: Python backend should process using AJAX
    alert('Circle drawn! Backend will compute average using center=' + center + ' and radius=' + radius);
}
map.on('draw:created', computeAverage);
"""
m.get_root().script.add_child(folium.Element(f"<script>{circle_avg_js}</script>"))


# --- Averaging with Pandas backend function ---
def average_in_circle(df, center_lat, center_lon, radius_km):
    from math import radians, cos, sin, asin, sqrt
    def haversine(lat1, lon1, lat2, lon2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return 6371*c
    filtered = df[df.apply(lambda r: haversine(center_lat, center_lon, r['lat'], r['lon']) <= radius_km, axis=1)]
    return filtered['utility_value'].mean()import requests



def chooseState() -> str:
    """Changes the url of the website to switch which state data you see
    Parameters:
        None
    Returns:
        str cooresponding to state name"""
    try:
        chosenState = input(f"Please type desired state:")
        chosenState = chosenState.lower()
        return chosenState
    except:
        print(f"There was some sort of error with chosenState(), defaulting to Texas.")
        return "texas"
 
def readWebsite():
    '''Reads all database APIs and gives cooresponding wanted data
    Parameters:
        None
    Returns:
        None'''
    chosenState = chooseState()
    outage_url = "https://poweroutage.us/area/state/texas" + chooseState
    
    # Houseing price API? https://www.zillow.com/research/data/
    
    
    try:
        response = requests.get(outage_url)
        result = response.json()
        info = sys.argv[1].lower()
        if info == "-h":
            
            
            # Need to adapt code from here
            print("Info options: s")
        else:
            wanted_info = result[info]
            print(wanted_info)
            print(type(wanted_info))
    except:
        if response.status_code == 404:
            print("Error: chosen state is not a correct state name")
        else:
            print("There was an error with the code...")

def main() -> None:
    readWebsite()

main()