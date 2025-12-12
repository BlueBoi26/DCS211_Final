US County API Interactive Map
Bates College DCS 211 F2025
Professor Barry Lawson
Made by: Fran Miele & Luke Hrinda

Description:
This program utilizes the US Cencus Bureau API to gather 13 different data categories and display them on an interactive map of the entire United States by county.
The 13 data categories are:
  Total Population
  Median Age
  White Population
  Black/African American Population
  Hispanic/Latino Population
  Asian Population
  Median Household Income
  Per Capita Income
  Persons in Poverty
  Unemployement Count
  Total Housing Units
  Median Gross Rent
  Median Home Value

Utilizing this data, a csv file is created of the data with the file CountyDataAPI.py. Then, Map.py loads in this csv to create a US map is created 
and displays all of the states. The map is interactable, and clickling on any state brings up a new map of just that states with the counties outlined.
From here, clicking on any county brings up the data about that area. If two or more counties are clicked on, the information instead shows the average values
between the multiple counties.
The user can then click on the same county again to deselect it, and click on the "Back to US Map" button to retrun to the entire map of the United States.

How to Use:
To run this program, first run the CountyDataAPI.py file to create county_data.csv. Then you can run Map.py to create all of the map html files to run locally on your device.
The final program should then automatically open in your browser and be fully interactable with the data already integrated.
