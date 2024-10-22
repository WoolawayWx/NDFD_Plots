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

# Load In Logos
logo1 = mpimg.imread('images/WEG_Black.png')
logo2 = mpimg.imread('images/WoolawayWx_Logo_Black.png')

# Load In Shapefiles
fname = 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp'
US_states_500k = ShapelyFeature(Reader(fname).geometries(), ccrs.PlateCarree(), facecolor='none')

fname2 = 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp'
US_highways = ShapelyFeature(Reader(fname2).geometries(), ccrs.PlateCarree(), facecolor='none')

fname3 = 'shapefiles/counties/cb_2018_us_county_5m.shp'
Counties = ShapelyFeature(Reader(fname3).geometries(), ccrs.PlateCarree(), facecolor='none')

file_path = 'NDFD_Data.xml'
tree = ET.parse(file_path)
root = tree.getroot()

lat = []
long = []
temps = []
towns = [ ... ]  # your list of towns
winds = []
rh = []

# Map Bounds
nlat = 37.25
slat = 36
wlon = -95.5
elon = -93
area = (wlon, elon, slat, nlat)

location_elements = root.findall('.//location')

for location in location_elements:
    lat.append(float(location[1].attrib['latitude']))
    long.append(float(location[1].attrib['longitude']))

# Get Weather Data
weather_params = root.findall('.//parameters')

for weatherdata in weather_params:
    rh.append(float(weatherdata[4][1].text))

# Interpolation Grid Setup
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_rh = griddata((long, lat), rh, (grid_lon, grid_lat), method='cubic')

data = list(zip(lat, long, temps, rh))

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2,
                                central_latitude=(slat + nlat) / 2,
                                standard_parallels=(30, 60))

# Define min/max temperature
# Define min/max relative humidity (RH) bounds
min_rh = 0   # Minimum relative humidity (0%)
max_rh = 100 # Maximum relative humidity (100%)

# Define the bounds, with a step of 5 (for 20 intervals)
bounds = np.arange(min_rh, max_rh + 5, 5)  # Include 100 in the bounds
levels = np.arange(0, 110, 10)
# Create a custom color map using a ListedColormap and custom colors
colors = [
    "#FF8C00",  # 0-10% Orange
    "#FFA500",  # 10-20% Yellow-orange
    "#FFD700",  # 20-30% Yellow
    "#ADFF2F",  # 30-40% Yellow-green
    "#00FF00",  # 40-50% Light green
    "#87CEEB",  # 50-60% Pale blue
    "#00BFFF",  # 60-70% Light blue
    "#0000FF",  # 70-80% Blue
    "#8A2BE2",  # 80-90% Purple
    "#FF69B4"   # 90-100% Pink
]
cmap = mcolors.ListedColormap(colors)

# Create a norm for the color boundaries
# norm = mcolors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)

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

ab1 = AnnotationBbox(imagebox1, (0.1, 0.1), xycoords='axes fraction', frameon=False, zorder=5)
ab2 = AnnotationBbox(imagebox2, (0.25, 0.1), xycoords='axes fraction', frameon=False, zorder=5)

ax.add_artist(ab1)
ax.add_artist(ab2)
# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_rh, transform=ccrs.PlateCarree(),
                      cmap=cmap, levels=levels, zorder=3, alpha=0.7)
plt.colorbar(contour, ax=ax, orientation='vertical', label='Relative Humidity (%)', shrink=0.5, ticks=ticker.MaxNLocator(integer=True))

with open('towns.json', 'r') as f:
    towns =json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Extract temperatures at town locations
for town, (lat_town, lon_town) in towns.items():
    # Find the nearest grid point
    dist, idx = tree.query([lon_town, lat_town])
    Loc_RHVal = grid_rh.flatten()[idx]

    # Plot town location and temperature
    ax.text(lon_town, lat_town, f'{town}',color='black', fontsize=5,
            transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{int(Loc_RHVal)}', color='black', fontsize=7,
            transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

plt.title('Forecasted Minimum Relative Humidity')
plt.savefig('map_rh.jpg', bbox_inches='tight', dpi=200)
