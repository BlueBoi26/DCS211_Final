import requests
import pandas as pd
import time

# --- CONFIGURATION ---
# Your API Key
API_KEY = "4416faddced3940d12388e16c5cb27ff03c9011b"

# The Dataset Year (2022 is the most recent full ACS 5-Year release as of late 2024)
YEAR = "2022"
DATASET = "acs/acs5"
BASE_URL = f"https://api.census.gov/data/{YEAR}/{DATASET}"

def get_census_data():
    print("--- US Census Data Downloader ---")
    print("This script fetches data for ALL counties in the US.")
    
    # Define the preset variables for the "ALL" command
    # These match the Cheat Sheet below perfectly.
    presets = {
        "Total Population": "B01003_001E",
        "Median Age": "B01002_001E",
        "White Alone": "B02001_002E",
        "Black/African American": "B02001_003E",
        "Hispanic or Latino": "B03003_003E",
        "Asian Alone": "B02001_005E",
        "Median Household Income": "B19013_001E",
        "Per Capita Income": "B19301_001E",
        "Persons in Poverty": "B17001_002E",
        "Unemployment Count": "B23025_005E",
        "Total Housing Units": "B25001_001E",
        "Median Gross Rent": "B25064_001E",
        "Median Home Value": "B25077_001E"
    }

    print("\n--- CHEAT SHEET: Common Variable Codes ---")
    print("  [Demographics]")
    print("  Total Population:          B01003_001E")
    print("  Median Age:                B01002_001E")
    print("  White Alone:               B02001_002E")
    print("  Black/African American:    B02001_003E")
    print("  Hispanic or Latino:        B03003_003E")
    print("  Asian Alone:               B02001_005E")
    
    print("\n  [Economics]")
    print("  Median Household Income:   B19013_001E")
    print("  Per Capita Income:         B19301_001E")
    print("  Persons in Poverty:        B17001_002E")
    print("  Unemployment Count:        B23025_005E")
    
    print("\n  [Housing]")
    print("  Total Housing Units:       B25001_001E")
    print("  Median Gross Rent:         B25064_001E")
    print("  Median Home Value:         B25077_001E")
    
    print("\n  [Shortcuts]")
    print("  Type 'ALL' to download every variable listed above.")
    print("------------------------------------------")
    
    # 1. Get User Input
    user_vars = input("\nEnter variable codes (separated by commas) OR type 'ALL': ").strip()
    
    # Check if user wants everything
    if user_vars.upper() == "ALL":
        print(f"\nCommand 'ALL' received. Selecting {len(presets)} variables...")
        variable_list = list(presets.values())
    else:
        # Clean up input (remove spaces)
        variable_list = [v.strip() for v in user_vars.split(',')]

    variable_string = ",".join(variable_list)
    
    # Add NAME so we know which county is which
    if "NAME" not in variable_list:
        variable_string = "NAME," + variable_string

    # 2. List of all US State FIPS codes
    state_fips = [
        "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", 
        "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", 
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", 
        "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56", "72"
    ]

    all_data = []

    print(f"\nStarting download...")
    
    # 3. Loop through every state
    for fips in state_fips:
        try:
            url = f"{BASE_URL}?get={variable_string}&for=county:*&in=state:{fips}&key={API_KEY}"
            
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                headers = data[0]
                rows = data[1:]
                
                # Create a mini DataFrame for this state
                state_df = pd.DataFrame(rows, columns=headers)
                all_data.append(state_df)
                
                print(f"Success: Retrieved data for State FIPS {fips}")
            else:
                print(f"Failed: State FIPS {fips} (Status: {response.status_code})")
                print(f"Error details: {response.text}")

        except Exception as e:
            print(f"Error processing state {fips}: {e}")
        
        # Pause to be polite to the server
        time.sleep(0.5)

    # 4. Combine all states into one big file
    if all_data:
        print("\nCombining data...")
        final_df = pd.concat(all_data, ignore_index=True)
        
        filename = "us_county_data.csv"
        final_df.to_csv(filename, index=False)
        print(f"DONE! Data saved to '{filename}' with {len(final_df)} rows.")
    else:
        print("No data was retrieved.")

if __name__ == "__main__":
    get_census_data()