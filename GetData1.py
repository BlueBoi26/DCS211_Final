import requests
import pandas as pd
import time
import warnings
import json

warnings.simplefilter(action='ignore', category=FutureWarning)

"""
DATASET DOCUMENTATION: combined_county_data.csv

1. fips_key (Census): Unique 5-digit county ID.
2. state_abbr: State Postal Code.
3. state_name (Census): State Name.
4. county_name (Census): County Name.
5. population (Census): Total Population.
6. median_income (Census): Median Household Income ($).
7. disaster_count (FEMA): Total federally declared disasters.
8. unemployment_rate (BLS): Unemployment rate (%).
9. obesity_rate (CDC): % of adults with obesity.
10. diabetes_rate (CDC): % of adults with diabetes.
11. smoking_rate (CDC): % of adults who smoke.
12. binge_drinking_rate (CDC): % of adults who binge drink.
"""

STATE_FIPS_MAP = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 
    'CO': '08', 'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13', 
    'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19', 
    'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24', 
    'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29', 
    'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34', 
    'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 
    'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50', 
    'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56',
    'DC': '11'
}


def fetch_census_data(state_fp):
    """Fetch Population and Income from Census."""
    base_url = "https://api.census.gov/data/2021/acs/acs5"
    params = {
        "get": "NAME,B01003_001E,B19013_001E",
        "for": "county:*",
        "in": f"state:{state_fp}"
    }
    
    cols = ["fips_key", "state_name", "county_name", "population", "median_income"]
    empty_df = pd.DataFrame(columns=cols)

    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [!] Census API Error: {e}")
        return empty_df

    if len(data) < 2:
        return empty_df

    df = pd.DataFrame(data[1:], columns=data[0])
    
    df.rename(columns={
        "B01003_001E": "population", 
        "B19013_001E": "median_income",
        "state": "state_fp",
        "county": "county_fp"
    }, inplace=True)

    df["population"] = pd.to_numeric(df["population"], errors='coerce').fillna(0).astype(int)
    df["median_income"] = pd.to_numeric(df["median_income"], errors='coerce')
    
    df["state_name"] = df["NAME"].str.split(", ").str[-1]
    df["county_name"] = df["NAME"].str.split(", ").str[0].str.replace(" County", "", regex=False)
    
    df["fips_key"] = df["state_fp"] + df["county_fp"]
    
    return df[cols]


def fetch_fema_disasters(state_postal):
    """Fetch disaster counts from FEMA API v2."""
    base_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
    params = {
        "$filter": f"state eq '{state_postal}'",
        "$select": "designatedArea",
        "$top": "10000" 
    }
    
    empty_df = pd.DataFrame(columns=["county_name", "disaster_count"])

    try:
        resp = requests.get(base_url, params=params)
        if resp.status_code == 404: return empty_df
        data = resp.json().get("DisasterDeclarationsSummaries", [])
    except Exception as e:
        print(f"  [!] FEMA API Error: {e}")
        return empty_df

    if not data: return empty_df

    df = pd.DataFrame(data)
    if "designatedArea" not in df.columns:
        return empty_df

    df["clean_county"] = df["designatedArea"].astype(str).str.replace(r" \(?County\)?", "", regex=True)
    
    counts = df.groupby("clean_county").size().reset_index(name="disaster_count")
    counts.rename(columns={"clean_county": "county_name"}, inplace=True)
    return counts


def fetch_bls_unemployment(state_fp, county_fips_list):
    """Fetch Unemployment Rate from BLS with conservative batching."""
    base_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {'Content-type': 'application/json'}
    
    empty_df = pd.DataFrame(columns=["fips_key", "unemployment_rate"])

    series_map = {} 
    for fips in county_fips_list:
        s_id = f"LAUCN{fips}0000000003"
        series_map[s_id] = fips

    all_series_ids = list(series_map.keys())
    
    batch_size = 20
    results = []

    for i in range(0, len(all_series_ids), batch_size):
        batch = all_series_ids[i:i + batch_size]
        payload = {
            "seriesid": batch,
            "startyear": "2023", 
            "endyear": "2023",
            "registrationkey": "" 
        }
        
        try:
            resp = requests.post(base_url, data=json.dumps(payload), headers=headers)
            data = resp.json()
            
            if data['status'] == 'REQUEST_SUCCEEDED':
                for series in data['Results']['series']:
                    sid = series['seriesID']
                    if series['data']:
                        val = series['data'][0]['value']
                        results.append({
                            "fips_key": series_map[sid], 
                            "unemployment_rate": float(val)
                        })
            else:
                print(f"    - Batch warning: {data.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"  [!] BLS API Batch Error: {e}")
        time.sleep(1)

    if not results:
        return empty_df
        
    return pd.DataFrame(results)


def fetch_cdc_places(state_abbr):
    """
    Fetch CDC PLACES Health Data.
    Uses 'locationid' (FIPS) for merging to avoid Name mismatches.
    """
    base_url = "https://data.cdc.gov/resource/swc5-untb.json"
    
    params = {
        "stateabbr": state_abbr,
        "$limit": 5000
    }
    
    expected_cols = ["fips_key", "obesity_rate", "diabetes_rate", "smoking_rate", "binge_drinking_rate"]
    empty_df = pd.DataFrame(columns=expected_cols)
    
    try:
        resp = requests.get(base_url, params=params)
        data = resp.json()
    except Exception as e:
        print(f"  [!] CDC API Error: {e}")
        return empty_df

    if not data: 
        return empty_df
    
    df = pd.DataFrame(data)
    
    df.columns = df.columns.str.lower()
    
    if "locationid" not in df.columns:
        print("  [!] CDC Warning: 'locationid' column missing. Merging may fail.")
        return empty_df
        
    target_measures = {
        "CSMOKING": "smoking_rate",
        "OBESITY": "obesity_rate",
        "DIABETES": "diabetes_rate",
        "BINGE": "binge_drinking_rate"
    }
    
    df = df[df["measureid"].isin(target_measures.keys())].copy()
    
    if df.empty:
        return empty_df
    
    pivot_df = df.pivot_table(
        index="locationid", 
        columns="measureid", 
        values="data_value", 
        aggfunc='first' 
    ).reset_index()
    
    pivot_df.rename(columns=target_measures, inplace=True)
    pivot_df.rename(columns={"locationid": "fips_key"}, inplace=True)
    
    for col in expected_cols:
        if col not in pivot_df.columns:
            pivot_df[col] = 0 
            
    return pivot_df


def main():
    print("--- STARTING DATA COLLECTION ---")
    
    states_to_process = ["CA", "IL", "TX"]
    final_dfs = []

    for state_postal in states_to_process:
        state_fp = STATE_FIPS_MAP.get(state_postal)
        if not state_fp: 
            print(f"Skipping {state_postal}: Invalid state code.")
            continue
            
        print(f"\nProcessing {state_postal} (FIPS: {state_fp})...")

        df_base = fetch_census_data(state_fp)
        if df_base.empty:
            print("  [x] Skipping state: Census fetch failed.")
            continue
        print(f"  - Census:   {len(df_base)} counties.")
        
        county_fips_list = df_base["fips_key"].tolist()

        df_fema = fetch_fema_disasters(state_postal)
        print(f"  - FEMA:     {len(df_fema)} records.")

        print("  - BLS:      Fetching unemployment (slow mode)...")
        df_bls = fetch_bls_unemployment(state_fp, county_fips_list)
        print(f"              {len(df_bls)} records.")

        df_cdc = fetch_cdc_places(state_postal)
        print(f"  - CDC:      {len(df_cdc)} records.")

        merged = pd.merge(df_base, df_fema, on="county_name", how="left")
        
        merged = pd.merge(merged, df_bls, on="fips_key", how="left")
        
        if not df_cdc.empty:
            df_cdc["fips_key"] = df_cdc["fips_key"].astype(str)
            merged = pd.merge(merged, df_cdc, on="fips_key", how="left")
        else:
            for col in ["obesity_rate", "diabetes_rate", "smoking_rate", "binge_drinking_rate"]:
                merged[col] = None

        merged["disaster_count"] = merged["disaster_count"].fillna(0).astype(int)
        merged["state_abbr"] = state_postal
        
        final_dfs.append(merged)
        time.sleep(1) 

    if final_dfs:
        full_df = pd.concat(final_dfs, ignore_index=True)
        
        cols = [
            "fips_key", "state_abbr", "state_name", "county_name", 
            "population", "median_income", "unemployment_rate",
            "disaster_count", 
            "obesity_rate", "diabetes_rate", "smoking_rate", "binge_drinking_rate"
        ]
        
        final_cols = [c for c in cols if c in full_df.columns]
        full_df = full_df[final_cols]

        print("\nSUCCESS: MERGED DATA SAMPLE")
        print(full_df.head(5))
        
        full_df.to_csv("combined_county_data.csv", index=False)
        print(f"\nSaved {len(full_df)} rows to 'combined_county_data.csv'.")
    else:
        print("\nNo data collected.")


if __name__ == "__main__":
    main()