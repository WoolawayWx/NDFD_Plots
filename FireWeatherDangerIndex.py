import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from matplotlib.colors import ListedColormap, BoundaryNorm
import requests
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import matplotlib.colors as colors
import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Load In Logos
logo1 = mpimg.imread('images/WEG_Black.png')
logo2 = mpimg.imread('images/WoolawayWx_Logo_Black.png')
# Load In Shapefiles
fname = 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp'
US_states_500k = ShapelyFeature(
    Reader(fname).geometries(), ccrs.PlateCarree(), facecolor='none')

fname2 = 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp'
US_highways = ShapelyFeature(
    Reader(fname2).geometries(), ccrs.PlateCarree(), facecolor='none')

fname3 = 'shapefiles/counties/cb_2018_us_county_5m.shp'
Counties = ShapelyFeature(Reader(fname3).geometries(),
                          ccrs.PlateCarree(), facecolor='none')

file_path = 'NDFD_Data.xml'
tree = ET.parse(file_path)
root = tree.getroot()

lat = []
long = []
temps = []
towns = [...]  # your list of towns
winds = []
FDI_Data = []
precip = []
MinRH = []
Winds_Sustained = []

TempFullSet = []
WindFullSet = []

# Map Bounds
nlat = 37.25
slat = 36
wlon = -95.5
elon = -93
area = (wlon, elon, slat, nlat)

# Varible Weights
Temp = 0.1
# Manual max is 0.15
Manual = 0.18
FuelMoisture_Var = 0.25
Wind_Sus = 0.125
Wind_Gusts = 0.175
MinRH_Var = 20

location_elements = root.findall('.//location')

for location in location_elements:
    lat.append(float(location[1].attrib['latitude']))
    long.append(float(location[1].attrib['longitude']))

# Get Weather Data
weather_params = root.findall('.//parameters')

# Temperature Impacts
for weatherdata in weather_params:
    TempFullSet.append(float(weatherdata[0][1].text))
    if float(weatherdata[0][1].text) >= 90:
        temps.append(100 * Temp / 100)
    elif float(weatherdata[0][1].text) >= 80:
        temps.append(50 * Temp / 100)
    elif float(weatherdata[0][1].text) >= 70:
        temps.append(20 * Temp / 100)
    else:
        temps.append(0 * Temp / 100)
# Precip Amounts
for weatherdata in weather_params:
    LocPrecipSum = float(
        weatherdata[1][1].text) + float(weatherdata[1][2].text) + float(weatherdata[1][3].text)
    precip.append(LocPrecipSum)
# Min RH%
for weatherdata in weather_params:
    LocDailyMinRH = float(weatherdata[4][1].text)
    if LocDailyMinRH <= 20:
        MinRH.append(100 * MinRH_Var * 0.01)
    elif 75 > LocDailyMinRH > 20:
        MinRH.append(((75 - LocDailyMinRH) / (75 - 20)) * MinRH_Var)
    elif LocDailyMinRH >= 75:
        MinRH.append(0 * MinRH_Var * 0.01)
    else:
        MinRH.append(0 * Temp)

# Wind Gusts
for weatherdata in weather_params:
    max_wind_gust = 0  # Start with the smallest possible number
    for x in range(1, len(weatherdata[3])-2):  # The range goes from 1 to 25
        LocWindGusts = float(weatherdata[3][x].text)
        # Update max_wind_gust if LocWindGusts is larger
        max_wind_gust = max(max_wind_gust, LocWindGusts)
# Convert to MPH.
    max_wind_gust = max_wind_gust * 1.15
    if float(max_wind_gust) > 35:
        winds.append(1 * Wind_Gusts)
    elif 15 < float(max_wind_gust) < 35:
        winds.append(((max_wind_gust - 15)/20) * Wind_Gusts)
    elif float(max_wind_gust) >= 10:
        winds.append(0)
    else:
        winds.append(0)

# Wind Sustained
for weatherdata in weather_params:
    max_wind_sus = 0  # Start with the smallest possible number

    # Loop through x from 1 to 25
    for z in range(1, len(weatherdata[2])-2):  # The range goes from 1 to 25
        LocWindSus = float(weatherdata[2][z].text)
        # Update max_wind_gust if LocWindGusts is larger
        max_wind_sus = max(max_wind_sus, LocWindSus)
# convert to MPH
    max_wind_sus = max_wind_sus * 1.15
    WindFullSet.append(max_wind_sus)
    if float(max_wind_sus) > 15:
        Winds_Sustained.append(100 * Wind_Sus * 0.01)
    elif 5 < float(max_wind_sus) < 15:
        Winds_Sustained.append(((15 - max_wind_sus) / (15 - 5)) * Wind_Sus)
    elif float(max_wind_sus) < 5:
        Winds_Sustained.append(0)
    else:
        Winds_Sustained.append(0)

# Fuel Moisture
url = "https://api.synopticdata.com/v2/stations/latest"
params = {
    'token': 'dbdc2dba77634cb99cd8969c2a75d708',
    'units': 'english',
    'output': 'json',
    'stid': 'CRWM7'
}
var_FM = 0
response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    fuel_moisture = data['STATION'][0]['OBSERVATIONS']['fuel_moisture_value_1']['value']
else:
    print(f"Error: {response.status_code}")

Cassville_FM = fuel_moisture

url = "https://api.synopticdata.com/v2/stations/latest"
params = {
    'token': 'dbdc2dba77634cb99cd8969c2a75d708',
    'units': 'english',
    'output': 'json',
    'stid': 'TT530'
}
var_FM = 0
response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    fuel_moisture = data['STATION'][0]['OBSERVATIONS']['fuel_moisture_value_1']['value']
else:
    print(f"Error: {response.status_code}")

Gateway_FM = fuel_moisture

url = "https://api.synopticdata.com/v2/stations/latest"
params = {
    'token': 'dbdc2dba77634cb99cd8969c2a75d708',
    'units': 'english',
    'output': 'json',
    'stid': 'MVVM7'
}
var_FM = 0
response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    fuel_moisture = data['STATION'][0]['OBSERVATIONS']['fuel_moisture_value_1']['value']
else:
    print(f"Error: {response.status_code}")

MtVernon_FM = fuel_moisture

fuel_moisture = (MtVernon_FM + Gateway_FM + Cassville_FM)/3
print('Current Fuel Moisture: ', fuel_moisture)

now = datetime.datetime.now()
nine_am = now.replace(hour=11, minute=0, second=0, microsecond=0)
avgforecasttemp = ((sum(TempFullSet)/len(TempFullSet)))
avgforecastwind = ((sum(WindFullSet)/len(WindFullSet)))
print(f"Avg Temp: {avgforecasttemp}")
print(f"Avg Wind: {avgforecastwind}")
if now < nine_am:
    fuel_moisture = fuel_moisture + -((fuel_moisture)/2*(((avgforecasttemp/90)/2)+((avgforecastwind/15)/2)))
    print('Forecasted Fuel Moisture: ', fuel_moisture)
else:
    print("It is 11 AM or later.")

if fuel_moisture > 20:
    fuel_moisture_input = 0
elif fuel_moisture > 15:
    fuel_moisture_input = 0.25 * FuelMoisture_Var
elif 5 < fuel_moisture < 15:
    weight = 95 - (fuel_moisture - 5) * 6.5
    fuel_moisture_input = (weight / 100) * FuelMoisture_Var
elif fuel_moisture < 5:
    fuel_moisture_input = 1 * FuelMoisture_Var

for i in range(0, len(temps)):
    datasum = temps[i] + (MinRH[i]/100) + winds[i] + \
        Winds_Sustained[i] + fuel_moisture_input + Manual
    FDI_Data.append(datasum)
# Custom Color Map
# Interpolation Grid Setup
grid_lon, grid_lat = np.meshgrid(np.linspace(
    wlon, elon, 5), np.linspace(slat, nlat, 5))
grid_FDIData = griddata((long, lat), FDI_Data,
                        (grid_lon, grid_lat), method='cubic')

data = list(zip(lat, long, FDI_Data))

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2,
                                central_latitude=(slat + nlat) / 2,
                                standard_parallels=(30, 60))


FDI_Colors = [
    (0.188, 0.651, 0.196),   # green
    (1.0, 0.984, 0.0),       # yellow
    (0.871, 0.537, 0.078),   # orange
    (0.902, 0.067, 0.067),   # red
    (0.902, 0.067, 0.761)    # pink
]

FDI_Levels = [0, 0.6, 0.7, 0.8, 0.9, 1]

cmap_FDI = LinearSegmentedColormap.from_list('cmap_FDI', FDI_Colors, N=5)
norm = colors.BoundaryNorm(boundaries=FDI_Levels, ncolors=256)

cmap_FDI_Colors = ListedColormap(FDI_Colors)
norm = BoundaryNorm(boundaries=FDI_Levels, ncolors=cmap_FDI_Colors.N)


fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=map_crs)
ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())

# Add map features
ax.add_feature(cfeature.LAND, zorder=1, edgecolor='k')
ax.add_feature(cfeature.STATES.with_scale('10m'), linewidth=1.0, zorder=2)
ax.add_feature(cfeature.BORDERS.with_scale('10m'), zorder=1)
ax.add_feature(US_states_500k, edgecolor='black', linewidth=1.0)
ax.add_feature(US_highways, edgecolor='red', linewidth=0.5)
ax.add_feature(Counties, edgecolor='gray', linewidth=0.75)

imagebox1 = OffsetImage(logo1, zoom=0.03)
imagebox2 = OffsetImage(logo2, zoom=0.03)

ab1 = AnnotationBbox(imagebox1, (0.1, 0.1),
                     xycoords='axes fraction', frameon=False, zorder=5)
ab2 = AnnotationBbox(imagebox2, (0.25, 0.1),
                     xycoords='axes fraction', frameon=False, zorder=5)

ax.add_artist(ab1)
ax.add_artist(ab2)

# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_FDIData, transform=ccrs.PlateCarree(),
                      cmap=cmap_FDI_Colors, zorder=3, alpha=0.7, norm=norm, levels=FDI_Levels)
co = ax.contour(grid_lon, grid_lat, grid_FDIData, transform=ccrs.PlateCarree(),
                colors='black', zorder=3, alpha=1, levels=FDI_Levels)
cbar = plt.colorbar(contour, ax=ax, orientation='vertical',
                    shrink=0.5, extend='both')
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
    # Find the nearest grid point
    dist, idx = tree.query([lon_town, lat_town])
    nearest_temp = grid_FDIData.flatten()[idx]

    # Plot town location and temperature
    ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5,
            transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{nearest_temp:.2f}', color='black', fontsize=7,
            transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')


# Get the date.
x = datetime.datetime.now()
date_day = x.strftime("%d")
todaysdate = f"{x.month}-{date_day}-{x.year}"
print(todaysdate)


plt.title(f'Forecasted Fire Danger Index | {todaysdate}')
plt.savefig('FWR.jpg', bbox_inches='tight', dpi=200)
