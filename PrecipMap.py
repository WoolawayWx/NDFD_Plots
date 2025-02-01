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
fname4 = 'shapefiles/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp'
World_Boundaries = ShapelyFeature(Reader(fname4).geometries(), ccrs.PlateCarree(), facecolor='none')

fname5 = 'shapefiles/ne_10m_land/ne_10m_land.shp'
Land = ShapelyFeature(Reader(fname5).geometries(), ccrs.PlateCarree(), facecolor='none')
file_path = 'NDFD_Data.xml'
tree = ET.parse(file_path)
root = tree.getroot()

lat = []
long = []
temps = []
towns = [ ... ]  # your list of towns
precip = []

# Map Bounds
nlat = 37.25
slat = 36
wlon = -95.5
elon = -93
area = (wlon, elon, slat, nlat)

precip_levels = [0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5]

location_elements = root.findall('.//location')

for location in location_elements:
    lat.append(float(location[1].attrib['latitude']))
    long.append(float(location[1].attrib['longitude']))

# Get Weather Data
weather_params = root.findall('.//parameters')

for weatherdata in weather_params:
    xmlPrcip = (float(weatherdata[1][1].text) + float(weatherdata[1][2].text) + float(weatherdata[1][3].text))
    precip.append(xmlPrcip)

# Interpolation Grid Setup
grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
grid_precip = griddata((long, lat), precip, (grid_lon, grid_lat), method='cubic')

data = list(zip(lat, long, precip, precip))

# Lambert Conformal Projection adjusted for your region
map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2,
                                central_latitude=(slat + nlat) / 2,
                                standard_parallels=(30, 60))

# Define min/max temperature
min_rainfall = min(precip)  # Minimum temperature
max_rainfall = max(precip)  # Maximum temperature

# Define the bounds (matching the numbers on your color bar)
#bounds = np.arange(min_rainfall, max_rainfall, ((max_rainfall-min_rainfall)/17))

# Create a custom color map using a ListedColormap and custom colors
# Need 11
colors = [
    "#a6ff94", "#5bb548", "#249c03", "#145901", "#ebdb50", "#e8e512", 
    "#e8ac3d", "#ef800a", "#d50c0c", "#cf1d1d", "#d613af", 
]
cmap = mcolors.ListedColormap(colors)

# Create a norm for the color boundaries
# norm = mcolors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)
norm = BoundaryNorm(boundaries=precip_levels, ncolors=cmap.N)

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=map_crs)
ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())

# Add map features
ax.add_feature(Land, zorder=1, edgecolor='k')
ax.add_feature(World_Boundaries, zorder=1)
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

contour = ax.contourf(grid_lon, grid_lat, grid_precip, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=3, alpha=0.7, levels=precip_levels)
cbar = plt.colorbar(contour, ax=ax, orientation='vertical', label='Forecasted Precipitation (IN)', shrink=0.5, ticks=ticker.MaxNLocator(integer=True))
cbar.set_ticks([0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5])
# Town coordinates (example)

with open('towns.json', 'r') as f:
    towns =json.load(f)

# KDTree for fast nearest neighbor search
grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
tree = cKDTree(grid_points)

# Extract temperatures at town locations
for town, (lat_town, lon_town) in towns.items():
    # Find the nearest grid point
    dist, idx = tree.query([lon_town, lat_town])
    LocPrecip = grid_precip.flatten()[idx]
    if(LocPrecip < 0):
        LocPrecip = 0.00
    # Plot town location and temperature
    ax.text(lon_town, lat_town, f'{town}',color='black', fontsize=5,
            transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
    ax.text(lon_town, lat_town, f'{LocPrecip:.2f}', color='black', fontsize=7,
            transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

todaysdate = datetime.now().strftime("%m-%d-%Y")
plt.title(f'Forecasted Precipitation | {todaysdate}')
plt.savefig('map_precip.jpg', bbox_inches='tight', dpi=200)