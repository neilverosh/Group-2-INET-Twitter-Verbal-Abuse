# -*- coding: utf-8 -*-
"""
Created on Tue Apr 19 18:56:56 2016

@authors: Neil Verosh and Sara Arango 
"""
# -- Load packages
import json
import geojson
import numpy as np
from shapely.geometry import Polygon

# -- Input data and input geometries
Tweets = geojson.loads(open('./input_files/Coordinates_15Keywords_Works.json').read()) # input Twitter data
State = geojson.loads(open('./input_files/us-counties.json').read()) # geometries and names of counties
County_pop = json.loads(open('./input_files/county-pop-FIPS-dict.json').read()) # counties with population
mention_list = json.loads(open('./input_files/twtCount-mentions.json').read()) # List and counts of mentions
hashtag_list = json.loads(open('./input_files/twtCount-hashtags.json').read()) # List and counts of hashtags

# -- Function to know if a point is inside a polygon. From http://www.ariel.com.au/a/python-point-int-poly.html
def point_inside_polygon(x,y,poly):
    n = len(poly)   
    inside =False
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    return inside


# -- Assigning a count of tweets per county where there was a tweet.
for county in County_pop['features']:
    county['twtDensity'] = {'Total':0.}
    county['centroid'] = []
    for mention in mention_list.keys():
        county['twtDensity'].update({mention: 0.})
    for hashtag in hashtag_list.keys():
        county['twtDensity'].update({hashtag: 0.})
for twt in Tweets:
    try:  
        y = twt['geo']['coordinates'][0]
        x = twt['geo']['coordinates'][1]
        #x= twt['coordinates']['coordinates'][0]
        #y= twt['coordinates']['coordinates'][1]
        for st in State['features']:
            for county in st['counties']:
                poly = county['geometry']['coordinates'][0]
                if len(np.shape(np.array(poly))) == 2:
                    if point_inside_polygon(x,y,poly):
                        #print "At least something is happening"
                        for c in County_pop['features']:
                            if c['county']==county['name']+" County" and c['state']==st['properties']['state']:
                                c['twtDensity']['Total'] += 1.
                                if twt['entities']['user_mentions']:
                                    for mt in twt['entities']['user_mentions']:
                                        for mention in mention_list.keys():
                                            if '@'+str(mt['screen_name']) == mention:
                                                c['twtDensity'][mention] += 1
                                if twt['entities']['hashtags']:
                                    for ht in twt['entities']['hashtags']:
                                        for hashtag in hashtag_list.keys():
                                            if '#'+str(ht['text']) == hashtag:
                                                c['twtDensity'][hashtag] += 1
                                        #twt['entities']['user_mentions']
                
    except  TypeError:
        print twt
        continue
# -- Creating a field for the geometry (centroid) of each county          
for st in State['features']:
    for county in st['counties']:
        poly = county['geometry']['coordinates'][0]
        if Polygon(poly).buffer(0).is_valid:
            try:
                pol_centroid = Polygon(poly).buffer(0).representative_point().wkt
                if len(np.shape(np.array(poly))) == 2:
                    for c in County_pop['features']:
                        if c['county']==county['name']+" County" and c['state']==st['properties']['state']:
                            c['centroid'] = [float(pol_centroid[7:24]),float(pol_centroid[25:-1])]
            except ValueError:
                    continue
          
          
# -- Normalizing offensive tweets by population           
tot_dens = {wrd:0.00 for wrd in County_pop['features'][0]['twtDensity'].keys()}
for county in County_pop['features']:
    if county['twtDensity']['Total'] != 0.00:
        for wrds,counts in county['twtDensity'].iteritems():
            if counts != 0.:
                county['twtDensity'][wrds] = float(counts) / float(county['population'])
                tot_dens[wrds] += county['twtDensity'][wrds]
for county in County_pop['features']:
    for wrds in county['twtDensity']:
        if tot_dens[wrds] != 0.:     
            if county['twtDensity'][wrds] != 0.0:                
                county['twtDensity'][wrds] = int(100.00*county['twtDensity'][wrds] / float(tot_dens[wrds]))


# -- Filling out and saving a dictionary to read from d3.   
us_cc = {'type':"FeatureCollection","features":[]}
cc = 0
for county in County_pop['features']:
    us_cc['features'].append({'type':'Feature','id':str(cc),'geometry':{'type':'Point','coordinates':county['centroid']},'properties':{'name':county['county'],'state':county['state'],'population':county['population'],'twtDensity':county['twtDensity']}}) # 'count':county['count']
    cc += 1      
with open('./input_files/twtDensity-counties.json', 'w') as fp:
   json.dump(us_cc, fp) 

"""
json_data1=open('us.json').read()
State = geojson.loads(json_data1)

def point_inside_polygon(x,y,poly):
# From http://www.ariel.com.au/a/python-point-int-poly.html

    n = len(poly)   
    inside =False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

json_data2=open('Tweets_Geolocation.json').read()
Tweets = geojson.loads(json_data2)

json_data3=open('centroids-tweets.json').read()
twtState = json.loads(json_data3)

for state in twtState['features']:
    state['properties']['count'] = 0. 

ct = 0
for twt in Tweets:
    x = twt['coordinates']['coordinates'][0]
    y = twt['coordinates']['coordinates'][1]
    ct += 1
    for st in State['features']:
        poly = st['geometry']['coordinates'][0]
        if len(np.shape(np.array(poly))) == 2:
            poly = st['geometry']['coordinates'][0]
            if point_inside_polygon(x,y,poly):
                for state in twtState['features']:
                    if state['properties']['name']==st['properties']['name']:
                        state['properties']['count'] += 1.  
                        
        elif len(np.shape(np.array(poly))) == 3:
            poly = st['geometry']['coordinates'][0][0]
            if point_inside_polygon(x,y,poly):
                for state in twtState['features']:
                    if state['properties']['name']==st['properties']['name']:
                        state['properties']['count'] += 1.    
            
tot_dens = 0.00
for state in twtState['features']:
    state['properties']['twtDensity'] = state['properties']['count'] / state['properties']['population']
    tot_dens += state['properties']['twtDensity']

for state in twtState['features']:
    state['properties']['twtDensity'] = int(100.00*state['properties']['twtDensity'] / tot_dens)
    
with open('twtDensity.json', 'w') as fp:
    json.dump(twtState, fp)
"""
    
"""  
dic = {'type': "FeatureCollection","features":[]}

for state in State['features']:
    dic['features'].append({'geometry': {'coordinates': state['geometry']['coordinates'], 'type': 'Polygon'}, 'type': 'Feature','properties':{'prop0': state['properties']['name'], 'prop1': {'this': 'that'}}})



{ "type": "FeatureCollection",
"features": [
    {"type": "Feature",
    "geometry": {
    "type": "Polygon",
    "coordinates": 

         },
         "properties": {
             "prop0": "value0",
             "prop1": {"this": "that"}
}}]}





{ "type": "FeatureCollection",
"features": [
    {"type": "Feature",
    "geometry": {
    "type": "Polygon",
    "coordinates": [
        [[-87.359296, 35.00118],
          [-85.606675, 34.984749],
          [-85.431413, 34.124869],
          [-85.184951, 32.859696],
          [-85.069935, 32.580372],
          [-84.960397, 32.421541],
          [-85.004212, 32.322956],
          [-84.889196, 32.262709],
          [-85.058981, 32.13674],
          [-85.053504, 32.01077],
          [-85.141136, 31.840985],
          [-85.042551, 31.539753],
          [-85.113751, 31.27686],
          [-85.004212, 31.003013],
          [-85.497137, 30.997536],
          [-87.600282, 30.997536],
          [-87.633143, 30.86609],
          [-87.408589, 30.674397],
          [-87.446927, 30.510088],
          [-87.37025, 30.427934],
          [-87.518128, 30.280057],
          [-87.655051, 30.247195],
          [-87.90699, 30.411504],
          [-87.934375, 30.657966],
          [-88.011052, 30.685351],
          [-88.10416, 30.499135],
          [-88.137022, 30.318396],
          [-88.394438, 30.367688],
          [-88.471115, 31.895754],
          [-88.241084, 33.796253],
          [-88.098683, 34.891641],
          [-88.202745, 34.995703],
          [-87.359296, 35.00118]]
          ]
         },
         "properties": {
             "prop0": "value0",
             "prop1": {"this": "that"}
}}]}

"""
