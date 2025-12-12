import requests
import pandas as pd
import time

API_KEY = "4416faddced3940d12388e16c5cb27ff03c9011b"
YEAR = "2022"
DATASET = "acs/acs5"
BASE_URL = f"https://api.census.gov/data/{YEAR}/{DATASET}"


def get_census_data():
    print("US Census Data Downloader")
    
    presets = {
        "Total Population": "B01003_001E",
        "Median Age": "B01002_001E",
        "White": "B02001_002E",
        "Black/African American": "B02001_003E",
        "Hispanic or Latino": "B03003_003E",
        "Asian": "B02001_005E",
        "Median Household Income": "B19013_001E",
        "Per Capita Income": "B19301_001E",
        "Persons in Poverty": "B17001_002E",
        "Unemployment Count": "B23025_005E",
        "Total Housing Units": "B25001_001E",
        "Median Gross Rent": "B25064_001E",
        "Median Home Value": "B25077_001E"
    }

    code_to_name = {v: k for k, v in presets.items()}
    
    code_to_name["NAME"] = "County Name"

    print("Variable Codes")
    print("Demographics:")
    print(f"  Total Population:          {presets['Total Population']}")
    print(f"  Median Age:                {presets['Median Age']}")
    print(f"  White:                     {presets['White']}")
    print(f"  Black/African American:    {presets['Black/African American']}")
    print(f"  Hispanic or Latino:        {presets['Hispanic or Latino']}")
    print(f"  Asian:                     {presets['Asian']}")
    print()
    print("Economics:")
    print(f"  Median Household Income:   {presets['Median Household Income']}")
    print(f"  Per Capita Income:         {presets['Per Capita Income']}")
    print(f"  Persons in Poverty:        {presets['Persons in Poverty']}")
    print(f"  Unemployment Count:        {presets['Unemployment Count']}")
    print()
    print("Housing:")
    print(f"  Total Housing Units:       {presets['Total Housing Units']}")
    print(f"  Median Gross Rent:         {presets['Median Gross Rent']}")
    print(f"  Median Home Value:         {presets['Median Home Value']}")
    print()
    print("  Type 'ALL' to download every variable listed above.")
    print()
    user_vars = input("Enter variable codes (separated by commas) or type 'ALL': ").strip()
    
    if user_vars.upper() == "ALL":
        print(f"User typed 'ALL'. Selecting {len(presets)} variables...")
        variable_list = list(presets.values())
    else:
        variable_list = [v.strip() for v in user_vars.split(',')]

    variable_string = ",".join(variable_list)
    
    if "NAME" not in variable_list:
        variable_string = "NAME," + variable_string

    state_fips = [
        "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", 
        "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", 
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", 
        "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56", "72"
    ]

    all_data = []
    print(f"\nStarting download...")

    for fips in state_fips:
        try:
            url = f"{BASE_URL}?get={variable_string}&for=county:*&in=state:{fips}&key={API_KEY}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                headers = data[0]
                rows = data[1:]
                
                state_df = pd.DataFrame(rows, columns=headers)
                all_data.append(state_df)
                print(f"Success: Retrieved data for State FIPS {fips}")
            else:
                print(f"Failed: State FIPS {fips} (Status: {response.status_code})")
        
        except Exception as e:
            print(f"Error processing state {fips}: {e}")
        
        time.sleep(0.5)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.rename(columns=code_to_name, inplace=True)
        
        filename = "county_data.csv"
        final_df.to_csv(filename, index=False)

        print(f"Data saved to '{filename}' with {len(final_df)} rows")
    else:
        print("No data was retrieved.")


if __name__ == "__main__":
    get_census_data()