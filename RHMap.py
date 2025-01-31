import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from matplotlib.colors import ListedColormap
import matplotlib.ticker as ticker
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
    'states': 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp',
    'highways': 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp',
    'counties': 'shapefiles/counties/cb_2018_us_county_5m.shp',
    'world_boundaries': 'shapefiles/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp',
    'land': 'shapefiles/ne_10m_land/ne_10m_land.shp'
}

features = {name: ShapelyFeature(Reader(path).geometries(), ccrs.PlateCarree(), facecolor='none') for name, path in shapefiles.items()}

# Parse XML Data
file_path = 'NDFD_Data.xml'
tree = ET.parse(file_path)
root = tree.getroot()

lat = [float(location[1].attrib['latitude']) for location in root.findall('.//location')]
long = [float(location[1].attrib['longitude']) for location in root.findall('.//location')]
rh = [float(weatherdata[4][1].text) for weatherdata in root.findall('.//parameters')]

# Interpolation Grid Setup
wlon, elon, slat, nlat = -95.5, -93, 36, 37.25
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_rh = griddata((long, lat), rh, (grid_lon, grid_lat), method='cubic')

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2,
                                central_latitude=(slat + nlat) / 2,
                                standard_parallels=(30, 60))

# Define min/max relative humidity (RH) bounds
bounds = np.arange(0, 105, 5)
levels = np.arange(0, 110, 10)
colors = [
    "#FF8C00", "#FFA500", "#FFD700", "#ADFF2F", "#00FF00",
    "#87CEEB", "#00BFFF", "#0000FF", "#8A2BE2", "#FF69B4"
]
cmap = mcolors.ListedColormap(colors)

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
ax.add_artist(AnnotationBbox(imagebox1, (0.1, 0.1), xycoords='axes fraction', frameon=False, zorder=5))
ax.add_artist(AnnotationBbox(imagebox2, (0.25, 0.1), xycoords='axes fraction', frameon=False, zorder=5))

# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_rh, transform=ccrs.PlateCarree(),
                      cmap=cmap, levels=levels, zorder=3, alpha=0.7)
plt.colorbar(contour, ax=ax, orientation='vertical', label='Relative Humidity (%)', shrink=0.5, ticks=ticker.MaxNLocator(integer=True))

with open('towns.json', 'r') as f:
    towns = json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Extract RH values at town locations
for town, (lat_town, lon_town) in towns.items():
    dist, idx = tree.query([lon_town, lat_town])
    Loc_RHVal = grid_rh.flatten()[idx]

    ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5,
            transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{int(Loc_RHVal)}', color='black', fontsize=7,
            transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

# Get the date.
todaysdate = datetime.now().strftime("%m-%d-%Y")
plt.title(f'Forecasted Minimum Relative Humidity | {todaysdate}')
plt.savefig('map_rh.jpg', bbox_inches='tight', dpi=200)
