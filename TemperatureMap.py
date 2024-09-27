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
import json

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
    temps.append(float(weatherdata[0][1].text))

# Interpolation Grid Setup
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_temps = griddata((long, lat), temps, (grid_lon, grid_lat), method='cubic')

data = list(zip(lat, long, temps))

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2,
                                central_latitude=(slat + nlat) / 2,
                                standard_parallels=(30, 60))

# Define min/max temperature
min_temp = min(temps) # Minimum temperature
max_temp = max(temps) # Maximum temperature

# Generate 100 temperature breaks
bounds = np.linspace(min_temp, max_temp, 100)
# Use the 'coolwarm' colormap for a smooth transition
cmap = plt.get_cmap('coolwarm', len(bounds))

# Create BoundaryNorm for the colormap
norm = BoundaryNorm(bounds, cmap.N)

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

# Contour plot
contour = ax.contourf(grid_lon, grid_lat, grid_temps, transform=ccrs.PlateCarree(),
                      cmap=cmap, norm=norm, zorder=3, alpha=0.7)
plt.colorbar(contour, ax=ax, orientation='vertical', label='Temperature (ºF)', shrink=0.5)

with open('towns.json', 'r') as f:
    towns =json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Extract temperatures at town locations
for town, (lat_town, lon_town) in towns.items():
    # Find the nearest grid point
    dist, idx = tree.query([lon_town, lat_town])
    nearest_temp = grid_temps.flatten()[idx]

    # Plot town location and temperature
    ax.text(lon_town, lat_town, f'{town}',color='black', fontsize=5,
            transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{int(nearest_temp)}', color='black', fontsize=7,
            transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

plt.title('Forecasted High Temperatures (ºF)')
plt.savefig('map_temp.jpg', bbox_inches='tight', dpi=200)
