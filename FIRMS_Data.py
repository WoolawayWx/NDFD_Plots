import requests
from datetime import datetime
import pandas as pd
from io import StringIO

# Define the bounding box for the states
bounding_box = {
    "Missouri": {"lat_min": 36.0, "lat_max": 40.6, "lon_min": -95.8, "lon_max": -89.1},
    "Oklahoma": {"lat_min": 33.6, "lat_max": 37.0, "lon_min": -103.0, "lon_max": -94.4},
    "Kansas": {"lat_min": 36.9, "lat_max": 40.0, "lon_min": -102.1, "lon_max": -94.6},
    "Arkansas": {"lat_min": 33.0, "lat_max": 36.5, "lon_min": -94.6, "lon_max": -89.6}
}

current_date = datetime.now().strftime("%Y-%m-%d")

# URLs for VIIRS and MODIS data
urls = {
    "VIIRS": f"https://firms.modaps.eosdis.nasa.gov/usfs/api/area/csv/f81a4a315bb6462e10f98548b71dc90c/VIIRS_NOAA20_NRT/world/1/{current_date}",
    "MODIS": f"https://firms.modaps.eosdis.nasa.gov/usfs/api/area/csv/f81a4a315bb6462e10f98548b71dc90c/MODIS_NRT/world/1/{current_date}"
}

dfs = []

for source, url in urls.items():
    response = requests.get(url)
    if response.status_code == 200:
        data = StringIO(response.text)
        df = pd.read_csv(data)
        dfs.append(df)
    else:
        print(f"Failed to retrieve data from {source}. HTTP Status code: {response.status_code}")

if dfs:
    combined_df = pd.concat(dfs, ignore_index=True)

    # Filter the data based on the bounding box
    filtered_df = combined_df[
        ((combined_df['latitude'] >= bounding_box["Missouri"]["lat_min"]) & (combined_df['latitude'] <= bounding_box["Missouri"]["lat_max"]) & 
         (combined_df['longitude'] >= bounding_box["Missouri"]["lon_min"]) & (combined_df['longitude'] <= bounding_box["Missouri"]["lon_max"])) |
        ((combined_df['latitude'] >= bounding_box["Oklahoma"]["lat_min"]) & (combined_df['latitude'] <= bounding_box["Oklahoma"]["lat_max"]) & 
         (combined_df['longitude'] >= bounding_box["Oklahoma"]["lon_min"]) & (combined_df['longitude'] <= bounding_box["Oklahoma"]["lon_max"])) |
        ((combined_df['latitude'] >= bounding_box["Kansas"]["lat_min"]) & (combined_df['latitude'] <= bounding_box["Kansas"]["lat_max"]) & 
         (combined_df['longitude'] >= bounding_box["Kansas"]["lon_min"]) & (combined_df['longitude'] <= bounding_box["Kansas"]["lon_max"])) |
        ((combined_df['latitude'] >= bounding_box["Arkansas"]["lat_min"]) & (combined_df['latitude'] <= bounding_box["Arkansas"]["lat_max"]) & 
         (combined_df['longitude'] >= bounding_box["Arkansas"]["lon_min"]) & (combined_df['longitude'] <= bounding_box["Arkansas"]["lon_max"]))
    ]

    filtered_df.to_csv("FIRMS_Data.csv", index=False)
    print("Filtered data saved to FIRMS_Data.csv")
else:
    print("Failed to retrieve data from both sources.")