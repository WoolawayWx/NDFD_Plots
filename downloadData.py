#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 10:17:12 2024

@author: cade
"""

import requests
from datetime import date, timedelta

print("Downloading Data...")
# Get today's date and 3 days later (72-hour period)
today = date.today()
end_day = today + timedelta(days=1)  # Extended to 72 hours

# Format the dates as 'YYYY-MM-DDTHH:MM:SS'
begin_date = today.strftime('%Y-%m-%dT00:00:00')
end_date = end_day.strftime('%Y-%m-%dT00:00:00')

# URL with placeholders for dynamic date insertion
url = ("https://digital.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?whichClient=NDFDgenSquare&lat=&lon=&listLatLon=&lat1=&lon1=&lat2=&lon2=&resolutionSub=&listLat1=&listLon1=&listLat2=&listLon2=&resolutionList=&endPoint1Lat=&endPoint1Lon=&endPoint2Lat=&endPoint2Lon=&listEndPoint1Lat=&listEndPoint1Lon=&listEndPoint2Lat=&listEndPoint2Lon=&zipCodeList=&listZipCodeList="
       "&centerPointLat=36.62&centerPointLon=-94&distanceLat=140.0&distanceLon=80.0&resolutionSquare=40.0&listCenterPointLat="
       "&listCenterPointLon=&listDistanceLat=&listDistanceLon=&listResolutionSquare=&citiesLevel=&listCitiesLevel=&sector="
       "&gmlListLatLon=&featureType=&requestedTime=&startTime=&endTime=&compType=&propertyName=&product=time-series&XMLformat="
       "DWML&begin={begin}&end={end}&Unit=e&maxt=maxt&wspd=wspd&wgust=wgust&qpf=qpf&minrh=minrh&Submit=Submit")

# Insert the dynamic dates into the URL
url_with_dates = url.format(begin=begin_date, end=end_date)

# Fetch the data from the URL
response = requests.get(url_with_dates)

# Save the response content as an XML file
with open('NDFD_Data.xml', 'wb') as file:
    file.write(response.content)

print('Data Downloaded')


