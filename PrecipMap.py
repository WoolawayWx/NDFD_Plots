import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree
from matplotlib.colors import BoundaryNorm
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
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
        'US_states_500k': 'shapefiles/states/ne_10m_admin_1_states_provinces_lines.shp',
        'US_highways': 'shapefiles/roads/US Primary/2023/tl_2023_us_primaryroads.shp',
        'Counties': 'shapefiles/counties/cb_2018_us_county_5m.shp',
        'World_Boundaries': 'shapefiles/ne_10m_admin_0_boundary_lines_land/ne_10m_admin_0_boundary_lines_land.shp',
        'Land': 'shapefiles/ne_10m_land/ne_10m_land.shp'
    }
    return {key: ShapelyFeature(Reader(fname).geometries(), ccrs.PlateCarree(), facecolor='none') for key, fname in shapefiles.items()}

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    lat = [float(location[1].attrib['latitude']) for location in root.findall('.//location')]
    long = [float(location[1].attrib['longitude']) for location in root.findall('.//location')]
    precip = [sum(float(weatherdata[1][i].text) for i in range(1, 4)) for weatherdata in root.findall('.//parameters')]
    return lat, long, precip

def create_grid(wlon, elon, slat, nlat, long, lat, precip):
    grid_lon, grid_lat = np.meshgrid(np.linspace(wlon, elon, 100), np.linspace(slat, nlat, 100))
    grid_precip = griddata((long, lat), precip, (grid_lon, grid_lat), method='cubic')
    return grid_lon, grid_lat, grid_precip

def plot_map(ax, shapefiles, grid_lon, grid_lat, grid_precip, cmap, norm, precip_levels, logos, towns, wlon, elon, slat, nlat):
    ax.set_extent([wlon, elon, slat, nlat], crs=ccrs.PlateCarree())
    ax.add_feature(shapefiles['Land'], zorder=1, edgecolor='k')
    ax.add_feature(shapefiles['World_Boundaries'], zorder=1)
    ax.add_feature(shapefiles['US_states_500k'], edgecolor='black', linewidth=1.0)
    ax.add_feature(shapefiles['US_highways'], edgecolor='red', linewidth=0.5)
    ax.add_feature(shapefiles['Counties'], edgecolor='gray', linewidth=0.75)

    imagebox1 = OffsetImage(logos[0], zoom=0.03)
    imagebox2 = OffsetImage(logos[1], zoom=0.03)
    ax.add_artist(AnnotationBbox(imagebox1, (0.1, 0.1), xycoords='axes fraction', frameon=False, zorder=5))
    ax.add_artist(AnnotationBbox(imagebox2, (0.25, 0.1), xycoords='axes fraction', frameon=False, zorder=5))

    contour = ax.contourf(grid_lon, grid_lat, grid_precip, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=3, alpha=0.7, levels=precip_levels)
    cbar = plt.colorbar(contour, ax=ax, orientation='vertical', label='Forecasted Precipitation (IN)', shrink=0.5, ticks=ticker.MaxNLocator(integer=True))
    cbar.set_ticks(precip_levels)

    grid_points = np.array([grid_lon.flatten(), grid_lat.flatten()]).T
    tree = cKDTree(grid_points)

    for town, (lat_town, lon_town) in towns.items():
        dist, idx = tree.query([lon_town, lat_town])
        LocPrecip = max(0.00, grid_precip.flatten()[idx])
        ax.text(lon_town, lat_town, f'{town}', color='black', fontsize=5, transform=ccrs.PlateCarree(), ha='center', va='top', fontweight='bold')
        ax.text(lon_town, lat_town, f'{LocPrecip:.2f}', color='black', fontsize=7, transform=ccrs.PlateCarree(), ha='center', va='bottom', fontweight='bold')

def main():
    logo1, logo2 = load_logos()
    shapefiles = load_shapefiles()
    lat, long, precip = parse_xml('NDFD_Data.xml')

    wlon, elon, slat, nlat = -95.5, -93, 36, 37.25
    grid_lon, grid_lat, grid_precip = create_grid(wlon, elon, slat, nlat, long, lat, precip)

    colors = ["#a6ff94", "#5bb548", "#249c03", "#145901", "#ebdb50", "#e8e512", "#e8ac3d", "#ef800a", "#d50c0c", "#cf1d1d", "#d613af"]
    cmap = mcolors.ListedColormap(colors)
    precip_levels = [0.01, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5]
    norm = BoundaryNorm(boundaries=precip_levels, ncolors=cmap.N)

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude=(wlon + elon) / 2, central_latitude=(slat + nlat) / 2, standard_parallels=(30, 60)))

    with open('towns.json', 'r') as f:
        towns = json.load(f)

    plot_map(ax, shapefiles, grid_lon, grid_lat, grid_precip, cmap, norm, precip_levels, (logo1, logo2), towns, wlon, elon, slat, nlat)

    todaysdate = datetime.now().strftime("%m-%d-%Y")
    plt.title(f'Forecasted Precipitation | {todaysdate}')
    plt.savefig('map_precip.jpg', bbox_inches='tight', dpi=200)

if __name__ == "__main__":
    main()
