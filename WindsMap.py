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
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import json
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime

# Load logos
logo1 = mpimg.imread('images/WEG_Black.png')
logo2 = mpimg.imread('images/WoolawayWx_Logo_Black.png')

# Load shapefiles
shapefiles = {
    'US_states': 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp',
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

lat, long, temps, winds = [], [], [], []

# Map bounds
nlat, slat, wlon, elon = 37.25, 36, -95.5, -93

# Extract location data
for location in root.findall('.//location'):
    lat.append(float(location[1].attrib['latitude']))
    long.append(float(location[1].attrib['longitude']))

# Extract weather data
for weatherdata in root.findall('.//parameters'):
    temps.append(float(weatherdata[0][1].text))
    max_wind = max(float(weatherdata[2][i].text) for i in range(1, 3))
    winds.append(max_wind * 1.1)

# Interpolation grid setup
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_winds = griddata((long, lat), winds, (grid_lon, grid_lat), method='cubic')

# Lambert Conformal Projection
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2, central_latitude=(slat + nlat) / 2, standard_parallels=(30, 60))

# Define color map and norm
min_windspeed, max_windspeed = min(winds), max(winds)
bounds = np.linspace(min_windspeed, max_windspeed, 18)
colors = [
    "#e6f7ff", "#cceeff", "#b3e6ff", "#99ccff", "#8099ff", "#9933ff", 
    "#cc33ff", "#ff33cc", "#ff3385", "#ff4d4d", "#ff6633", "#ff9933", 
    "#ffcc33", "#ffff00", "#e6b800", "#cc6600", "#994d00"
]
cmap = ListedColormap(colors)
norm = BoundaryNorm(bounds, cmap.N, clip=True)

# Plot setup
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': map_crs})
ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())

# Add map features
for feature in features.values():
    ax.add_feature(feature, edgecolor='black', linewidth=1.0 if feature == features['US_states'] else 0.75)

# Add logos
for logo, pos in zip([logo1, logo2], [(0.1, 0.1), (0.25, 0.1)]):
    imagebox = OffsetImage(logo, zoom=0.03)
    ab = AnnotationBbox(imagebox, pos, xycoords='axes fraction', frameon=False, zorder=5)
    ax.add_artist(ab)

# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_winds, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=3, alpha=0.7)
plt.colorbar(contour, ax=ax, orientation='vertical', label='Wind Speed (MPH)', shrink=0.5, ticks=ticker.MaxNLocator(integer=True))

# Load towns data
with open('towns.json', 'r') as f:
    towns = json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Plot town locations and wind speeds
for town, (lat_town, lon_town) in towns.items():
    dist, idx = tree.query([lon_town, lat_town])
    WindGusts = grid_winds.flatten()[idx]
    ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5, transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{int(WindGusts)}', color='black', fontsize=7, transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

# Add title and save plot
todaysdate = datetime.now().strftime("%m-%d-%Y")
plt.title(f'Forecasted Highest Sustained Winds | {todaysdate}')
plt.savefig('map_winds.jpg', bbox_inches='tight', dpi=200)
