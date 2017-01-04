import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

## The first area I chose to audit was the city values in the OSM data##
OSMFILE = "Newbury Area OSM 281116.osm"
city_check_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

## After auditing the cities, I added the below list to the cities_expected as the values in the represent correct values/part of values in this area ##
cities_expected = ["Aldermaston", "Andover", "Ash", "Avington", "Basildon", "Basingstoke", "Bedwyn",
                   "Bradfield", "Bramley", "Caversham", "Chaddleworth", "Checkendon", "Curridge", "Goring", 
                   "Hook", "Hungerford", "Ilsley", "Inkpen", "Ipsden", "Kingsclere", "Kintbury", 
                   "Mapledurham", "Marlborough", "Midgham", "Mortimer", "Newbury", "Norreys", "Overton", "Pangbourne", 
                   "Shinfield", "Streatley-On-Thames", "Swindon", "Theale", "Common", "Hill", "Row", "Tadley"
                  ]
## I have added a small number of mappings to correct a small number of values including some that had multiple cities present in the same field ##

city_mapping = { 
            "READING" : "Reading",
            "THATCHAM" : "Thatcham",
            "Rotherfield Greys / Henley-on-Thames" : "Henley-on-Thames",
            "Caversham, Reading" : "Reading",
            "Lower Basildon, Reading" : "Reading",
            "Pangbourne, Reading" : "Reading"
            }  

def audit_cities(city_values, city_name):
    m = city_check_re.search(city_name)
    if m:
        cities = m.group()
        if cities not in cities_expected:
            city_values[cities].add(city_name)

def is_city(elem):
    return (elem.attrib['k'] == "addr:city")  

def audit_cityvalues(OSMFILE):
    osm_file = open(OSMFILE, "r")
    city_values = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):      
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_city(tag):
                    audit_cities(city_values, tag.attrib['v'])
    osm_file.close
    return city_values

def update_cities(name, mapping):
    m = city_check_re.search(name)
    if m:
        cities = m.group()
        if cities in city_mapping.keys():
            name = re.sub(m.group(), mapping[m.group()],name)
    return name


## The second area I chose to audit was the street names in the OSM data ##

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
num_line_street_re = re.compile(r'\d0?(st|nd|rd|th|)\s(Line)$', re.IGNORECASE) # Spelling out numbers in streets rather than using numbers
nth_re = re.compile(r'\d\d?(st|nd|rd|th|)', re.IGNORECASE)
nesw_re = re.compile(r'\s(North|East|South|West)$')

## After auditing the street names, I added the below list to the expected values as they are geniune street names ##
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Close", "Gardens", "Hill", "Way", "Park", "Centre", 
            "Common", "Crescent", "Fields", "Roundabout", "Row", "Ride", "View", "Walk",
            "Broadway", "Down", "End", "Grove", "Cornfields", "Eastcourt", "Green", "Link",
            "Mill", "Newfound", "A339", "Fosbury", "Glebe", "Hailey", "Rookery", "Smithy", "Parade",
            "Arcade", "Estate", "Mall", "Rise", "Horse", "West", "Mead", "Approach", "Ashbury", "Brow",
            "Butts", "By-pass", "Chase", "Cottages", "Forbury", "Forest", "Gate", "Heath", "Lea",
            "Market", "Mews", "Oracle", "Pleasant", "Queensway", "Saye", "Terrace", "Tilehurst", "Limes"]

## I added the below corrections to the mapping table to insure that incorrect values are correctly dealt with ##
mapping = { 
            "Rd" : "Road",
            "Rd," : "Road",
            "Road," : "Road",
            "Steet" : "Street",
            "Road," : "Road",
            "Steet" : "Street",
            "Ave" : "Avenue",
            "Sr" : "Street",
            "street" : "Street",
            "www.cpva.org.uk" : "Unknown"
            }  

street_mapping = { 
            "Rd" : "Road",
            "Rd," : "Road",
            "Road," : "Road",
            "Steet" : "Street",
            "Road," : "Road",
            "Steet" : "Street",
            "Ave" : "Avenue",
            "Sr" : "Street",
            "street" : "Street",
            "www.cpva.org.uk" : "Unknown"
            }  

num_line_mapping = {
                     "1st": "First",
                     "2nd": "Second",
                     "3rd": "Third",
                     "4th": "Fourth",
                     "5th": "Fifth",
                     "6th": "Sixth",
                     "7th": "Seventh",
                     "8th": "Eighth",
                     "9th": "Ninth",
                     "10th": "Tenth"
                   }

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street") 
    ## Used the OSM Wiki to find the sub tag for streets

def audit_street(OSMFILE):
    osm_file = open(OSMFILE, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):      
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close
    return street_types 
    
def update_name(name):

    if num_line_street_re.match(name):
        nth = nth_re.search(name)
        name = num_line_mapping[nth.group(0)] + " Line"
        return name

    else:
        original_name = name
        for key in mapping.keys():
            # Only replace when mapping key match (e.g. "St.") is found at end of name
            type_fix_name = re.sub(r'\s' + re.escape(key) + r'$', ' ' + mapping[key], original_name)
            nesw = nesw_re.search(type_fix_name)
            if nesw is not None:
                for key in street_mapping.keys():
                    # Do not update correct names like St. Clair Avenue West
                    dir_fix_name = re.sub(r'\s' + re.escape(key) + re.escape(nesw.group(0)), " " + street_mapping[key] + nesw.group(0), type_fix_name)
                    if dir_fix_name != type_fix_name:
                        # print original_name + "=>" + type_fix_name + "=>" + dir_fix_name
                        return dir_fix_name
            if type_fix_name != original_name:
                # print original_name + "=>" + type_fix_name
                return type_fix_name
    # Check if avenue, road, street, etc. are capitalized
    last_word = original_name.rsplit(None, 1)[-1]
    if last_word.islower():
        original_name = re.sub(last_word, last_word.title(), original_name)
    return original_name
