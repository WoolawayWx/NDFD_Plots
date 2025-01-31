import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from matplotlib.colors import BoundaryNorm
import json
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime

def load_logos():
    logo1 = mpimg.imread('images/WEG_Black.png')
    logo2 = mpimg.imread('images/WoolawayWx_Logo_Black.png')
    return logo1, logo2

def load_shapefiles():
    shapefiles = {
        'US_states': 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp',
        'US_highways': 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp',
        'Counties': 'shapefiles/counties/cb_2018_us_county_5m.shp',
        'World_Boundaries': 'shapefiles/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp',
        'Land': 'shapefiles/ne_10m_land/ne_10m_land.shp'
    }
    features = {name: ShapelyFeature(Reader(path).geometries(), ccrs.PlateCarree(), facecolor='none') for name, path in shapefiles.items()}
    return features

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root

def extract_location_data(root):
    lat, long = [], []
    location_elements = root.findall('.//location')
    for location in location_elements:
        lat.append(float(location[1].attrib['latitude']))
        long.append(float(location[1].attrib['longitude']))
    return lat, long

def extract_weather_data(root):
    temps = []
    weather_params = root.findall('.//parameters')
    for weatherdata in weather_params:
        temps.append(float(weatherdata[0][1].text))
    return temps

def create_interpolation_grid(wlon, elon, slat, nlat, long, lat, temps):
    grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
    grid_temps = griddata((long, lat), temps, (grid_lon, grid_lat), method='cubic')
    return grid_lon, grid_lat, grid_temps

def plot_map(features, grid_lon, grid_lat, grid_temps, wlon, elon, slat, nlat, min_temp, max_temp, logos, towns):
    map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2, central_latitude=(slat + nlat) / 2, standard_parallels=(30, 60))
    bounds = np.linspace(min_temp, max_temp, 100)
    cmap = plt.get_cmap('coolwarm', len(bounds))
    norm = BoundaryNorm(bounds, cmap.N)

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(1, 1, 1, projection=map_crs)
    ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())

    for feature in features.values():
        ax.add_feature(feature, zorder=1, edgecolor='k')

    imagebox1 = OffsetImage(logos[0], zoom=0.03)
    imagebox2 = OffsetImage(logos[1], zoom=0.03)
    ab1 = AnnotationBbox(imagebox1, (0.1, 0.1), xycoords='axes fraction', frameon=False, zorder=5)
    ab2 = AnnotationBbox(imagebox2, (0.25, 0.1), xycoords='axes fraction', frameon=False, zorder=5)
    ax.add_artist(ab1)
    ax.add_artist(ab2)

    contour = ax.contourf(grid_lon, grid_lat, grid_temps, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=3, alpha=0.7)
    plt.colorbar(contour, ax=ax, orientation='vertical', label='Temperature (ºF)', shrink=0.5)

    grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
    tree = cKDTree(grid_points)

    for town, (lat_town, lon_town) in towns.items():
        dist, idx = tree.query([lon_town, lat_town])
        nearest_temp = grid_temps.flatten()[idx]
        ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5, transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
        ax.text(lon_town, lat_town, f'{int(nearest_temp)}', color='black', fontsize=7, transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

    x = datetime.now()
    todaysdate = f"{x.month}-{x.day}-{x.year}"
    plt.title(f'Forecasted High Temperatures (ºF) | {todaysdate}')
    plt.savefig('map_temp.jpg', bbox_inches='tight', dpi=200)

def main():
    logos = load_logos()
    features = load_shapefiles()
    root = parse_xml('NDFD_Data.xml')
    lat, long = extract_location_data(root)
    temps = extract_weather_data(root)
    wlon, elon, slat, nlat = -95.5, -93, 36, 37.25
    grid_lon, grid_lat, grid_temps = create_interpolation_grid(wlon, elon, slat, nlat, long, lat, temps)
    min_temp, max_temp = min(temps), max(temps)

    with open('towns.json', 'r') as f:
        towns = json.load(f)

    plot_map(features, grid_lon, grid_lat, grid_temps, wlon, elon, slat, nlat, min_temp, max_temp, logos, towns)

if __name__ == "__main__":
    main()
