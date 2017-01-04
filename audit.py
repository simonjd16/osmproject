## After auditing the street names I have added to the expected list based on local knowledge
## Corrections are also required to abbreviations present in the data set to correctly map them the expect value

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "Newbury Area OSM 281116.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
num_line_street_re = re.compile(r'\d0?(st|nd|rd|th|)\s(Line)$', re.IGNORECASE) # Spelling out numbers in streets rather than using numbers
nth_re = re.compile(r'\d\d?(st|nd|rd|th|)', re.IGNORECASE)
nesw_re = re.compile(r'\s(North|East|South|West)$')

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Close", "Gardens", "Hill", "Way", "Park", "Centre", 
            "Common", "Crescent", "Fields", "Roundabout", "Row", "Ride", "View", "Walk",
            "Broadway", "Down", "End", "Grove", "Cornfields", "Eastcourt", "Green", "Link",
            "Mill", "Newfound", "A339", "Fosbury", "Glebe", "Hailey", "Rookery", "Smithy", "Parade",
            "Arcade", "Estate", "Mall", "Rise", "Horse", "West", "Mead"]

mapping = { 
            "Rd" : "Road",
            "Road," : "Road",
            "Steet" : "Street",
            "Rd'" : "Road",
            "Road," : "Road",
            "Steet" : "Street",
            "Ave" : "Avenue",
            "Sr" : "Street"
            }  

street_mapping = { 
            "Rd" : "Road",
            "Road," : "Road",
            "Steet" : "Street",
            "Rd'" : "Road",
            "Road," : "Road",
            "Steet" : "Street",
            "Ave" : "Avenue",
            "Sr" : "Street"
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
    """
    Clean street name for insertion into SQL database
    """
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
