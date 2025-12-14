US County API Interactive Map

Bates College — DCS 211 (Fall 2025)\*\*
Professor: Barry Lawson
Created by: Fran Miele and Luke Hrinda

---

Project Goal and Scope

This project is a local, interactive data visualization tool designed to explore U.S. Census Bureau county-level data across the entire United States. The program retrieves demographic, economic, and housing data for all U.S. counties, stores that data in a CSV file, and presents it through an interactive, browser-based map.

The scope of the project is limited to read-only data exploration. Users may select and compare counties visually, but the program does not modify or persist data, perform time-series analysis, or provide predictive modeling. All maps are generated and served locally using a simple HTTP server.

Data Description

The program gathers 13 Census data categories for each U.S. county:

Total Population
Median Age
White Population
Black/African American Population
Hispanic/Latino Population
Asian Population
Median Household Income
Per Capita Income
Persons in Poverty
Unemployment Count
Total Housing Units
Median Gross Rent
Median Home Value

Program Structure

This project consists of two primary Python scripts:

`CountyDataAPI.py`

- Uses the U.S. Census Bureau API to retrieve county-level data
- Collects and normalizes the 13 data categories
- Outputs the results to a CSV file named `county_data.csv`

`Map.py`

- Loads `county_data.csv` using Pandas
- Uses the Folium library to generate interactive Leaflet maps
- Creates:

  - One national-level map of U.S. states
  - One county-level map for each individual state

- Embeds JavaScript for interactivity, including state navigation and county selection
- Starts a local web server to display the generated HTML maps

Required Libraries and Dependencies

The following non-default Python libraries are required to run this project:

- folium
- pandas
- requests

All other imports used in the project (such as `json`, `threading`, `http.server`, and `webbrowser`) are part of the Python standard library.

Installation Instructions

Install the required libraries using pip:

```bash
pip install folium pandas requests
```

How to Run the Program

1. First, run the data collection script:

```bash
python CountyDataAPI.py
```

This will generate a file named `county_data.csv` containing Census data for all U.S. counties.

2. Next, run the map generation and server script:

```bash
python Map.py
```

3. The program will:

   - Generate all HTML map files in the current directory
   - Start a local HTTP server at `http://localhost:8000`
   - Automatically open the main U.S. map in your default web browser

4. To stop the program, return to the terminal and press Ctrl + C.

How to Use the Interactive Map

- Click on any state to open a county-level map for that state.
- Click on a county to select it and view its Census data in the information panel.
- Click the same county again to deselect it.
- Select multiple counties to view averaged Census statistics across all selected counties.
- Use the “Back to US Map” link to return to the national map.

Features and Example Outputs

- State-level navigation: Clicking on California opens a map displaying only California counties.
- County selection: Clicking on Los Angeles County highlights the county and displays its population, income, and housing data.
- Multi-county comparison: Selecting both Los Angeles County and San Diego County displays averaged Census values across the two counties.
- Visual feedback: Selected counties are highlighted in blue, and selection updates dynamically.

Output Files

- `county_data.csv` — Census data collected from the API
- `us_states_map.html` — Interactive national map
- `county_map_<State_Name>.html` — One county-level map per state

All files are generated automatically when the program runs.

Limitations

- The application must be run locally and is not deployed to a public server.
- Data reflects a single snapshot from the Census API and does not support historical comparisons.
- Performance may vary depending on system resources due to the number of generated map files.
