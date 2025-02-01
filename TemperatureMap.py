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

def main():
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
    
    # Parse XML
    root = ET.parse('NDFD_Data.xml').getroot()
    
    # Extract location and weather data
    lat, long, temps = [], [], []
    for location in root.findall('.//location'):
        lat.append(float(location[1].attrib.get('latitude', 0)))
        long.append(float(location[1].attrib.get('longitude', 0)))
    for weatherdata in root.findall('.//parameters'):
        temps.append(float(weatherdata[0][1].text))
    
    # Interpolation Grid
    wlon, elon, slat, nlat = -95.5, -93, 36, 37.25
    grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
    grid_temps = griddata((long, lat), temps, (grid_lon, grid_lat), method='cubic')
    
    # Plot Map
    map_crs = ccrs.LambertConformal(central_longitude=(wlon + elon) / 2, central_latitude=(slat + nlat) / 2, standard_parallels=(30, 60))
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': map_crs})
    ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())
    for name, feature in features.items():
        edgecolor = 'brown' if name == 'US_highways' else 'k'
        linewidth = 0.25 if name == 'US_highways' else 1.0
        ax.add_feature(feature, edgecolor=edgecolor)
    
    # Add logos
    ax.add_artist(AnnotationBbox(OffsetImage(logo1, zoom=0.03), (0.1, 0.1), xycoords='axes fraction', frameon=False))
    ax.add_artist(AnnotationBbox(OffsetImage(logo2, zoom=0.03), (0.25, 0.1), xycoords='axes fraction', frameon=False))
    
    # Contour plot
    cmap = plt.get_cmap('coolwarm', 100)
    norm = BoundaryNorm(np.linspace(min(temps), max(temps), 100), cmap.N)
    contour = ax.contourf(grid_lon, grid_lat, grid_temps, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, alpha=0.7)
    plt.colorbar(contour, ax=ax, orientation='vertical', label='Temperature (ºF)', shrink=0.5)
    
    # Load and plot towns
    with open('towns.json', 'r') as f:
        towns = json.load(f)
    tree = cKDTree(np.array([grid_lon.flatten(), grid_lat.flatten()]).T)
    for town, (lat_town, lon_town) in towns.items():
        dist, idx = tree.query([lon_town, lat_town])
        nearest_temp = grid_temps.flatten()[idx]
        ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5, transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
        ax.text(lon_town, lat_town, f'{int(nearest_temp)}', color='black', fontsize=7, transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')
    
    # Save figure
    plt.title(f'Forecasted High Temperatures (ºF) | {datetime.now().strftime("%m-%d-%Y")}')
    plt.savefig('map_temp.jpg', bbox_inches='tight', dpi=200)
    
if __name__ == "__main__":
    print('Running Main')
    main()