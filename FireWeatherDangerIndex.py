import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap
import requests
from datetime import datetime
import json
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Load In Logos
logo1 = mpimg.imread('images/WEG_Black.png')
logo2 = mpimg.imread('images/WoolawayWx_Logo_Black.png')

# Load In Shapefiles
shapefiles = {
    'states': 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp',
    'highways': 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp',
    'counties': 'shapefiles/counties/cb_2018_us_county_5m.shp',
    'world_boundaries': 'shapefiles/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp',
    'land': 'shapefiles/ne_10m_land/ne_10m_land.shp'
}

features = {key: ShapelyFeature(Reader(fname).geometries(), ccrs.PlateCarree(), facecolor='none') for key, fname in shapefiles.items()}

# Parse XML data
file_path = 'NDFD_Data.xml'
tree = ET.parse(file_path)
root = tree.getroot()

lat, long, temps, winds, FDI_Data, precip, MinRH, Winds_Sustained = [], [], [], [], [], [], [], []
TempFullSet, WindFullSet = [], []

# Map Bounds
nlat, slat, wlon, elon = 37.25, 36, -95.5, -93

# Variable Weights
weights = {
    'Temp': 0.1,
    'Manual': 0.16,
    'FuelMoisture_Var': 0.25,
    'Wind_Sus': 0.125,
    'Wind_Gusts': 0.175,
    'MinRH_Var': 20
}

# Extract location data
location_elements = root.findall('.//location')
lat = [float(location[1].attrib['latitude']) for location in location_elements]
long = [float(location[1].attrib['longitude']) for location in location_elements]

# Get Weather Data
weather_params = root.findall('.//parameters')

# Temperature Impacts
for weatherdata in weather_params:
    temp = float(weatherdata[0][1].text)
    TempFullSet.append(temp)
    if temp >= 90:
        temps.append(100 * weights['Temp'] / 100)
    elif temp >= 80:
        temps.append(50 * weights['Temp'] / 100)
    elif temp >= 70:
        temps.append(20 * weights['Temp'] / 100)
    else:
        temps.append(0)

# Precip Amounts
precip = [sum(float(weatherdata[1][i].text) for i in range(1, 4)) for weatherdata in weather_params]

# Min RH%
for weatherdata in weather_params:
    LocDailyMinRH = float(weatherdata[4][1].text)
    if LocDailyMinRH <= 20:
        MinRH.append(100 * weights['MinRH_Var'] * 0.01)
    elif 75 > LocDailyMinRH > 20:
        MinRH.append(((75 - LocDailyMinRH) / (75 - 20)) * weights['MinRH_Var'])
    else:
        MinRH.append(0)

# Wind Gusts
for weatherdata in weather_params:
    max_wind_gust = max(float(weatherdata[3][x].text) for x in range(1, len(weatherdata[3])-2)) * 1.15
    if max_wind_gust > 35:
        winds.append(1 * weights['Wind_Gusts'])
    elif 15 < max_wind_gust < 35:
        winds.append(((max_wind_gust - 15)/20) * weights['Wind_Gusts'])
    else:
        winds.append(0)

# Wind Sustained
for weatherdata in weather_params:
    max_wind_sus = max(float(weatherdata[2][z].text) for z in range(1, len(weatherdata[2])-2)) * 1.15
    WindFullSet.append(max_wind_sus)
    if max_wind_sus > 15:
        Winds_Sustained.append(100 * weights['Wind_Sus'] * 0.01)
    elif 5 < max_wind_sus < 15:
        Winds_Sustained.append(((15 - max_wind_sus) / (15 - 5)) * weights['Wind_Sus'])
    else:
        Winds_Sustained.append(0)

# Fuel Moisture
def get_fuel_moisture(station_id):
    url = "https://api.synopticdata.com/v2/stations/latest"
    params = {
        'token': 'dbdc2dba77634cb99cd8969c2a75d708',
        'units': 'english',
        'output': 'json',
        'stid': station_id
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['STATION'][0]['OBSERVATIONS']['fuel_moisture_value_1']['value']
    else:
        print(f"Error: {response.status_code}")
        return None

stations = ['CRWM7', 'TT530', 'MVVM7']
fuel_moisture_values = [get_fuel_moisture(station) for station in stations]
fuel_moisture = sum(fuel_moisture_values) / len(fuel_moisture_values)
print('Current Fuel Moisture: ', fuel_moisture)

now = datetime.now()
nine_am = now.replace(hour=11, minute=30, second=0, microsecond=0)
avgforecasttemp = sum(TempFullSet) / len(TempFullSet)
avgforecastwind = sum(WindFullSet) / len(WindFullSet)
print(f"Avg Temp: {avgforecasttemp}")
print(f"Avg Wind: {avgforecastwind}")

if now < nine_am:
    fuel_moisture += -((fuel_moisture)/2*(((avgforecasttemp/90)/2)+((avgforecastwind/15)/2)))
    print('Forecasted Fuel Moisture: ', fuel_moisture)
else:
    print("It is 11 AM or later.")

if fuel_moisture > 20:
    fuel_moisture_input = 0
elif fuel_moisture > 15:
    fuel_moisture_input = 0.25 * weights['FuelMoisture_Var']
elif 5 < fuel_moisture < 15:
    weight = 95 - (fuel_moisture - 5) * 6.5
    fuel_moisture_input = (weight / 100) * weights['FuelMoisture_Var']
else:
    fuel_moisture_input = 1 * weights['FuelMoisture_Var']

for i in range(len(temps)):
    datasum = temps[i] + (MinRH[i]/100) + winds[i] + Winds_Sustained[i] + fuel_moisture_input + weights['Manual']
    FDI_Data.append(datasum)

# Custom Color Map
FDI_Colors = [
    (0.188, 0.651, 0.196),   # green
    (1.0, 0.984, 0.0),       # yellow
    (0.871, 0.537, 0.078),   # orange
    (0.902, 0.067, 0.067),   # red
    (0.902, 0.067, 0.761)    # pink
]

FDI_Levels = [0, 0.6, 0.7, 0.8, 0.9, 1]
cmap_FDI = LinearSegmentedColormap.from_list('cmap_FDI', FDI_Colors, N=5)
norm = BoundaryNorm(boundaries=FDI_Levels, ncolors=cmap_FDI.N)

# Interpolation Grid Setup
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_FDIData = griddata((long, lat), FDI_Data, (grid_lon, grid_lat), method='cubic')

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2, central_latitude=(slat + nlat) / 2, standard_parallels=(30, 60))

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=map_crs)
ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())

# Add map features
ax.add_feature(features['land'], zorder=1, edgecolor='k')
ax.add_feature(features['world_boundaries'], zorder=1)
ax.add_feature(features['states'], edgecolor='black', linewidth=1.0)
ax.add_feature(features['highways'], edgecolor='red', linewidth=0.5)
ax.add_feature(features['counties'], edgecolor='gray', linewidth=0.75)

imagebox1 = OffsetImage(logo1, zoom=0.03)
imagebox2 = OffsetImage(logo2, zoom=0.03)

ab1 = AnnotationBbox(imagebox1, (0.1, 0.1), xycoords='axes fraction', frameon=False, zorder=5)
ab2 = AnnotationBbox(imagebox2, (0.25, 0.1), xycoords='axes fraction', frameon=False, zorder=5)

ax.add_artist(ab1)
ax.add_artist(ab2)

# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_FDIData, transform=ccrs.PlateCarree(), cmap=cmap_FDI, zorder=3, alpha=0.7, norm=norm, levels=FDI_Levels)
co = ax.contour(grid_lon, grid_lat, grid_FDIData, transform=ccrs.PlateCarree(), colors='black', zorder=3, alpha=1, levels=FDI_Levels)
cbar = plt.colorbar(contour, ax=ax, orientation='vertical', shrink=0.5, extend='both')
cbar.set_ticks([0.3, 0.65, 0.75, 0.85, 0.95])
cbar.ax.set_yticklabels(['Low', 'Moderate', 'High', 'Very High', 'Extreme'])

# Town coordinates (example)
with open('towns.json', 'r') as f:
    towns = json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Extract temperatures at town locations
for town, (lat_town, lon_town) in towns.items():
    dist, idx = tree.query([lon_town, lat_town])
    nearest_temp = grid_FDIData.flatten()[idx]

    ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5, transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{nearest_temp:.2f}', color='black', fontsize=7, transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

# Get the date.
todaysdate = datetime.now().strftime("%m-%d-%Y")
plt.title(f'Forecasted Fire Danger Index | {todaysdate}')

plt.savefig('map_FWR.jpg', bbox_inches='tight', dpi=200)
