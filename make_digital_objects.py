#!/usr/bin/env python

###############################################################################
#
# make_digital_objects.py -- make a bunch of digital object records at once
#
# Takes as input the URI for whatever series contains the digitized material,
# as well as a list of handles/file names (in CSV), and constructs digital
# objects from the data it finds
#
###############################################################################

import re, os, errno, json, csv
from asnake.aspace import ASpace

AS = ASpace()
repo = AS.repositories(2)

def get_uri():
    uri = input('Enter the URI for the component containing your digitized items: ')
    if not re.compile('^\/repositories\/2\/(resources|archival_objects)\/\d+$').match(uri):
        raise ValueError("URI must belong to a Resource or Archival Object")
    return uri

def get_json(uri):
    r = AS.client.get(uri)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        r.raise_for_status()

def build_list(uri):
    list = {}

    children = get_json("{}/children".format(uri))
    for child in children:
        key = child['component_id']
        list[key] = {
            'uri': child['uri'],
            'title': child['display_string'],
            'file_versions': []
        }

        # identifiers.csv is how we assign the handles as digital_object_ids;
        # row[0] is the Sound Model ID, row[1] is the handle
        if os.path.exists('identifiers.csv'):
            with open('identifiers.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if key == row[0]:
                        list[key]['digital_object_id'] = row[1]

    return list

def link_object(ao, do):
    item = get_json(ao)

    # append digital object instance to the item and make it representative
    item['instances'].append({
        'instance_type': 'digital_object',
        'jsonmodel_type': 'instance',
        'is_representative': True,
        'digital_object': { 'ref': do }
    })

    r = AS.client.post(ao,json=item)
    message = json.loads(r.text)
    if r.status_code == 200:
        print("{}: {}".format(message['status'], message['uri']))
    else:
        print("Error: {}".format(message['error']))

uri = get_uri()
print("Building the tree... ")
list = build_list(uri)

###############################################################################
#
# Whatever your CSV is named, it should have one row per *file*, and contain
# two columns:
#
# * Column 1 contains the component ID for the item to which the file belongs
# * Column 2 contains the file name
#
# A component's digital object may contain more than one file.
#
# The script will iterate over the CSV file and append the file metadata to
# whatever item is specified in column 1.
#
###############################################################################

file = input('Enter the name of the file containing your digital object file names: ')
if os.path.exists(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] in list:
                list[row[0]]['file_versions'].append({
                    'file_uri': row[1],
                    'caption': row[1],
                    'file_format_name': 'wav',
                    'jsonmodel_type': 'file_version'
                })
            else:
                print("No item with this call number: {}".format(row[0]))
else:
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file)

for key in list:
    item = list[key]['uri']
    object = {
        'title': list[key]['title'],
        'digital_object_type': 'sound_recording',
        'jsonmodel_type': 'digital_object',
        'file_versions': list[key]['file_versions']
    }

    if 'digital_object_id' in list[key].keys():
        object['digital_object_id'] = list[key]['digital_object_id']
    else:
        object['digital_object_id'] = key

    r = AS.client.post('/repositories/2/digital_objects',json=object)
    message = json.loads(r.text)
    if r.status_code == 200:
        digital_object = message['uri']

        # link_object function accepts the URIs for the item and digital object; links the latter to the former
        link_object(item, digital_object)
    else:
        print("Error: {}".format(message['error']))
