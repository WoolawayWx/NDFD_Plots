import requests
from datetime import date, timedelta
import xml.etree.ElementTree as ET

print("Spot Forecast Request")

# Input for latitude, longitude, department, date, and time
Lat = float(input("Lat: "))
Lon = float(input("Lon: "))
if(Lon > 0):
    Lon = -Lon
Department = input("Department Requesting: ")
Date = input("Enter the date (YYYY-MM-DD): ")

print("Times must be current day, and must follow 24 hour format. Ex. 1400")
StartTime = input("Start Time (HHMM): ")
EndTime = input("End Time (HHMM): ")

# Format the start and end time to include the date for URL
BeginTime = f"{Date}T{StartTime[:2]}:{StartTime[2:]}:00"
EndTimeFormatted = f"{Date}T{EndTime[:2]}:{EndTime[2:]}:00"

# Create the URL
url = (f"https://digital.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?whichClient=NDFDgenSquare"
       f"&lat={Lat}&lon={Lon}&listLatLon=&lat1=&lon1=&lat2=&lon2=&resolutionSub=&listLat1=&listLon1=&listLat2=&listLon2="
       f"&resolutionList=&endPoint1Lat=&endPoint1Lon=&endPoint2Lat=&endPoint2Lon=&listEndPoint1Lat=&listEndPoint1Lon="
       f"&listEndPoint2Lat=&listEndPoint2Lon=&zipCodeList=&listZipCodeList=&centerPointLat={Lat}&centerPointLon={Lon}"
       f"&distanceLat=140.0&distanceLon=80.0&resolutionSquare=40.0&listCenterPointLat=&listCenterPointLon=&listDistanceLat="
       f"&listDistanceLon=&listResolutionSquare=&citiesLevel=&listCitiesLevel=&sector=&gmlListLatLon=&featureType=&requestedTime="
       f"&startTime=&endTime=&compType=&propertyName=&product=time-series&XMLformat=DWML&begin={BeginTime}&end={EndTimeFormatted}"
       f"&Unit=e&maxt=maxt&wspd=wspd&wgust=wgust&qpf=qpf&minrh=minrh&Submit=Submit")

# Output the request information and the generated URL

response = requests.get(url)

with open('SpotForecastData.xml', 'wb') as file:
    file.write(response.content)

file_path = 'SpotForecastData.xml'
tree = ET.parse(file_path)
root = tree.getroot()

weather_params = root.findall('.//parameters')

for weatherdata in weather_params:
    LocPrecipSum = 0  # Initialize the sum to 0
    MaxTemp = -40
    # Loop over each relevant element in the weatherdata[1] list starting from index 1
    for i in range(1, len(weatherdata[1])): 
        LocPrecipSum += float(weatherdata[1][i].text)  # Add each value to LocPrecipSum

    print(f"Total Precipitation: {LocPrecipSum}")
    for i in range(1, len(weatherdata[0])): 
        if(float(weatherdata[0][i].text) > MaxTemp):
            MaxTemp = float(weatherdata[0][i].text)
    print(f"Max Daily High: {MaxTemp}")