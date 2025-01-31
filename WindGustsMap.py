import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
import matplotlib.colors as mcolors
import json
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime

# Load In Logos
logo1 = mpimg.imread('images/WEG_Black.png')
logo2 = mpimg.imread('images/WoolawayWx_Logo_Black.png')

# Load In Shapefiles
shapefiles = {
    'US_states_500k': 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp',
    'US_highways': 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp',
    'Counties': 'shapefiles/counties/cb_2018_us_county_5m.shp',
    'World_Boundaries': 'shapefiles/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp',
    'Land': 'shapefiles/ne_10m_land/ne_10m_land.shp'
}

features = {name: ShapelyFeature(Reader(path).geometries(), ccrs.PlateCarree(), facecolor='none') for name, path in shapefiles.items()}

# Parse XML data
file_path = 'NDFD_Data.xml'
tree = ET.parse(file_path)
root = tree.getroot()

lat, long, winds = [], [], []

# Map Bounds
nlat, slat, wlon, elon = 37.25, 36, -95.5, -93
area = (wlon, elon, slat, nlat)

# Extract location data
for location in root.findall('.//location'):
    lat.append(float(location[1].attrib['latitude']))
    long.append(float(location[1].attrib['longitude']))

# Extract weather data
for weatherdata in root.findall('.//parameters'):
    max_wind = max(float(weatherdata[3][i].text) for i in range(1, 3))
    winds.append(max_wind * 1.1)

# Interpolation Grid Setup
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_winds = griddata((long, lat), winds, (grid_lon, grid_lat), method='cubic')

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2, central_latitude=(slat + nlat) / 2, standard_parallels=(30, 60))

# Define min/max windspeed
min_windspeed, max_windspeed = min(winds), max(winds)

# Define the bounds (matching the numbers on your color bar)
bounds = np.arange(min_windspeed, max_windspeed, ((max_windspeed - min_windspeed) / 17))

# Create a custom color map using a ListedColormap and custom colors
colors = [
    "#e6f7ff", "#cceeff", "#b3e6ff", "#99ccff", "#8099ff", "#9933ff", 
    "#cc33ff", "#ff33cc", "#ff3385", "#ff4d4d", "#ff6633", "#ff9933", 
    "#ffcc33", "#ffff00", "#e6b800", "#cc6600", "#994d00"
]
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=map_crs)
ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())

# Add map features
for feature in features.values():
    ax.add_feature(feature, zorder=1, edgecolor='k')

imagebox1 = OffsetImage(logo1, zoom=0.03)
imagebox2 = OffsetImage(logo2, zoom=0.03)
ab1 = AnnotationBbox(imagebox1, (0.1, 0.1), xycoords='axes fraction', frameon=False, zorder=5)
ab2 = AnnotationBbox(imagebox2, (0.25, 0.1), xycoords='axes fraction', frameon=False, zorder=5)
ax.add_artist(ab1)
ax.add_artist(ab2)

# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_winds, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=3, alpha=0.7)
plt.colorbar(contour, ax=ax, orientation='vertical', label='Wind Speed (MPH)', shrink=0.5)

# Load town data
with open('towns.json', 'r') as f:
    towns = json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Extract wind gusts at town locations
for town, (lat_town, lon_town) in towns.items():
    dist, idx = tree.query([lon_town, lat_town])
    WindGusts = grid_winds.flatten()[idx]
    ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5, transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{int(WindGusts)}', color='black', fontsize=7, transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

# Get the date
todaysdate = datetime.now().strftime("%m-%d-%Y")
plt.title(f'Forecasted Max Wind Gusts | {todaysdate}')
plt.savefig('map_windgusts.jpg', bbox_inches='tight', dpi=200)
