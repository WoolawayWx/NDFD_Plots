import pandas as pd
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

# Load the data
data = pd.read_csv('/Users/cade/WoolawayWx/_Dev/Forecast/NDFD Plot Maps/FIRMS_Data.csv')

# Extract latitude and longitude
latitudes = data['latitude']
longitudes = data['longitude']

# Create a map
plt.figure(figsize=(12, 8))
m = Basemap(projection='merc', llcrnrlat=-60, urcrnrlat=90, llcrnrlon=-180, urcrnrlon=180, resolution='c')

# Draw coastlines and countries
m.drawcoastlines()
m.drawcountries()

# Convert latitude and longitude to map coordinates
x, y = m(longitudes.values, latitudes.values)

# Plot the data points
m.scatter(x, y, marker='o', color='red', zorder=5)

# Add a title
plt.title('FIRMS Data Plot')

# Save the plot as an image
plt.savefig('/Users/cade/WoolawayWx/_Dev/Forecast/NDFD Plot Maps/FIRMS_Data_Plot.png')

# Show the plot
plt.show()