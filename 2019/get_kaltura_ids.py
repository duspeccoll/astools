#!/usr/bin/env python

##########
#
# get_kaltura_ids.py -- get Kaltura IDs from a bulk ingest log XML file
#
# Feed this script an XML log file of a Kaltura bulk ingest; it will scan the
# Reference ID (if it's a digital_object_component URI), download the object
# found at that URI, and add the Kaltura entry ID to it
#
##########

import argparse
import json
import os
from lxml import etree
from asnake.aspace import ASpace

ap = argparse.ArgumentParser(description='Add or update ArchivesSpace metadata properties from CSV input')
ap.add_argument('-f', '--file', help='The CSV file containing the metadata to add')
args = ap.parse_args()

AS = ASpace()

def get_json(uri):
    r = AS.client.get(uri)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        r.raise_for_status()


def post_json(uri, data):
    r = AS.client.post(uri,json=data)
    message = json.loads(r.text)
    if r.status_code == 200:
        print("{}: {}".format(message['status'], message['uri']))
    else:
        print("Error: {}".format(message['error']))


if args.file:
    if os.path.exists(args.file):
        parser = etree.XMLParser(remove_blank_text=True)
        with open(args.file, 'r') as xml:
            data = etree.parse(xml, parser).getroot()
            for item in data.xpath('channel/item'):
                component_id = item.find('customData/metadata/ReferenceID').text
                kaltura_id = item.find('entryId').text
                print("{} has kaltura ID {}".format(component_id, kaltura_id))
                obj = get_json(component_id)
                obj['component_id'] = kaltura_id
                post_json(component_id, obj)
    else:
        print("File not found: {}".format(args.file))
else:
    print("No file provided")
