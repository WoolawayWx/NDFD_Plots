#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 10:17:12 2024

@author: cade
"""

import requests

zipcodes = '64861+65625+65708+64831+72756+72764+64850+64801+65705+65806+65747+65616+72632+74344+74354'
begindate = '2024-08-27'
enddate = '2024-08-28'

# Define the URL to fetch the data
url = ("https://digital.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?whichClient=NDFDgenSquare&lat=&lon=&listLatLon=&lat1=&lon1=&lat2=&lon2=&resolutionSub=&listLat1=&listLon1=&listLat2=&listLon2=&resolutionList=&endPoint1Lat=&endPoint1Lon=&endPoint2Lat=&endPoint2Lon=&listEndPoint1Lat=&listEndPoint1Lon=&listEndPoint2Lat=&listEndPoint2Lon=&zipCodeList=&listZipCodeList=&centerPointLat=36.62&centerPointLon=-94&distanceLat=140.0&distanceLon=80.0&resolutionSquare=40.0&listCenterPointLat=&listCenterPointLon=&listDistanceLat=&listDistanceLon=&listResolutionSquare=&citiesLevel=&listCitiesLevel=&sector=&gmlListLatLon=&featureType=&requestedTime=&startTime=&endTime=&compType=&propertyName=&product=time-series&XMLformat=DWML&begin=2024-08-29T00%3A00%3A00&end=2024-08-30T00%3A00%3A00&Unit=e&maxt=maxt&wspd=wspd&critfireo=critfireo&wgust=wgust&Submit=Submit")

# Fetch the data from the URL
response = requests.get(url)

# Save the response content as an XML file
with open('NDFD_Data.xml', 'wb') as file:
    file.write(response.content)

print('Data Downloaded')
