import requests
import sys
import json

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