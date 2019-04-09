#!/usr/bin/env python

###############################################################################
#
# make_digital_objects.py -- make a bunch of digital object records at once
#
# Takes as input the URI for whatever series contains the digitized material,
# as well as a list of handles/file names (in CSV), and constructs digital
# objects from the data it finds
#
# I haven't spec'd out exactly how this stuff should be formatted but I will;
# it's usually my last thought on these one-off scripts...
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

    return list

def link_object(ao, do):
    item = get_json(ao)
    item['instances'].append({
        'instance_type': 'digital_object',
        'jsonmodel_type': 'instance',
        'digital_object': { 'ref': do }
    })

    r = AS.client.post(ao,json=item)
    message = json.loads(r.text)
    if r.status_code == 200:
        print("{}: {}".format(message['status'], message['uri']))
    else:
        print("Error: {}".format(message['error']))

uri = get_uri()
list = build_list(uri)

file = input('Enter the name of the file containing your digital object file names: ')
if os.path.exists(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            list[row[0]]['file_versions'].append({
                'file_uri': row[1],
                'caption': row[1],
                'file_format_name': 'wav',
                'jsonmodel_type': 'file_version'
            })
else:
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file)

for key in list:
    item = list[key]['uri']
    object = {
        'digital_object_id': key,
        'title': list[key]['title'],
        'digital_object_type': 'sound_recording',
        'jsonmodel_type': 'digital_object',
        'file_versions': list[key]['file_versions']
    }
    r = AS.client.post('/repositories/2/digital_objects',json=object)
    message = json.loads(r.text)
    if r.status_code == 200:
        digital_object = message['uri']
        link_object(item, digital_object)
    else:
        print("Error: {}".format(message['error']))
