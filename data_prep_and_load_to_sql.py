## Preparing the data for transfering into SQL
import csv
import codecs
import re
import xml.etree.cElementTree as ET

import cerberus

OSM_PATH = "Newbury Area OSM 31102016.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
POSTCODE = re.compile(r'[A-z]\d[A-z]\s?\d[A-z]\d')

city_check_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
num_line_street_re = re.compile(r'\d0?(st|nd|rd|th|)\s(Line)$', re.IGNORECASE) # Spelling out numbers in streets rather than using numbers
nth_re = re.compile(r'\d\d?(st|nd|rd|th|)', re.IGNORECASE)
nesw_re = re.compile(r'\s(North|East|South|West)$')

SCHEMA = schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Close", "Gardens", "Hill", "Way", "Park", "Centre", 
            "Common", "Crescent", "Fields", "Roundabout", "Row", "Ride", "View", "Walk",
            "Broadway", "Down", "End", "Grove", "Cornfields", "Eastcourt", "Green", "Link",
            "Mill", "Newfound", "A339", "Fosbury", "Glebe", "Hailey", "Rookery", "Smithy", "Parade",
            "Arcade", "Estate", "Mall", "Rise", "Horse", "West", "Mead", "Approach", "Ashbury", "Brow",
            "Butts", "By-pass", "Chase", "Cottages", "Forbury", "Forest", "Gate", "Heath", "Lea",
            "Market", "Mews", "Oracle", "Pleasant", "Queensway", "Saye", "Terrace", "Tilehurst", "Limes"]

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

cities_expected = ["Aldermaston", "Andover", "Ash", "Avington", "Basildon", "Basingstoke", "Bedwyn",
                   "Bradfield", "Bramley", "Caversham", "Chaddleworth", "Checkendon", "Curridge", "Goring", 
                   "Hook", "Hungerford", "Ilsley", "Inkpen", "Ipsden", "Kingsclere", "Kintbury", 
                   "Mapledurham", "Marlborough", "Midgham", "Mortimer", "Newbury", "Norreys", "Overton", "Pangbourne", 
                   "Shinfield", "Streatley-On-Thames", "Swindon", "Theale", "Common", "Hill", "Row", "Tadley"
                  ]

city_mapping = { 
            "READING" : "Reading",
            "THATCHAM" : "Thatcham",
            "Rotherfield Greys / Henley-on-Thames" : "Henley-on-Thames",
            "Caversham, Reading" : "Reading",
            "Lower Basildon, Reading" : "Reading",
            "Pangbourne, Reading" : "Reading"
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
    osm_file.close()
    return street_types

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

def load_new_tag(element, secondary, default_tag_type):
## Load a new tag dict to go into the list of dicts for way_tags, node_tags ##
    new = {}
    new['id'] = element.attrib['id']
    if ":" not in secondary.attrib['k']:
        new['key'] = secondary.attrib['k']
        new['type'] = default_tag_type
    else:
        post_colon = secondary.attrib['k'].index(":") + 1
        new['key'] = secondary.attrib['k'][post_colon:]
        new['type'] = secondary.attrib['k'][:post_colon - 1]
 ## Cleaning and loading values of various keys for both street names and cities
    if is_street_name(secondary):
        street_name = update_name(secondary.attrib['v'])
        new['value'] = street_name
    elif is_city(secondary):
        city_name = update_name(secondary.attrib['v'])
        new['value'] = city_name
    else:
        new['value'] = secondary.attrib['v']
    
    return new

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
##Clean and shape node or way XML element to Python dict##

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for attrib, value in element.attrib.iteritems():
            if attrib in node_attr_fields:
                node_attribs[attrib] = value
        
        ## For elements within the top element
        for secondary in element.iter():
            if secondary.tag == 'tag':
                if problem_chars.match(secondary.attrib['k']) is not None:
                    continue
                else:
                    new = load_new_tag(element, secondary, default_tag_type)
                    if new is not None:
                        tags.append(new)
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        for attrib, value in element.attrib.iteritems():
            if attrib in way_attr_fields:
                way_attribs[attrib] = value

        counter = 0
        for secondary in element.iter():
            if secondary.tag == 'tag':
                if problem_chars.match(secondary.attrib['k']) is not None:
                    continue
                else:
                    new = load_new_tag(element, secondary, default_tag_type)
                    if new is not None:
                        tags.append(new)
            elif secondary.tag == 'nd':
                newnd = {}
                newnd['id'] = element.attrib['id']
                newnd['node_id'] = secondary.attrib['ref']
                newnd['position'] = counter
                counter += 1
                way_nodes.append(newnd)
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)

####
