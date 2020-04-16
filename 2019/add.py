#!/usr/bin/env python

import argparse
import csv
import json
import os
from asnake.aspace import ASpace

AS = ASpace()
repo = AS.repositories(2)

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help="A CSV list of URIs to pass to the script")
args = parser.parse_args()

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


def post_digital_object(uri, row, obj):
    dao = {
        'title': obj['display_string'],
        'digital_object_type': "text",
        'jsonmodel_type': "digital_object",
        'publish': True,
        'file_versions': []
    }

    dao['digital_object_id'] = row[1]
    dao['file_versions'].append({
        'file_uri': "{}.pdf".format(row[0]),
        'file_format_type': "pdf",
        'publish': True
    })

    r = AS.client.post("/repositories/2/digital_objects", json=dao)
    message = json.loads(r.text)
    if r.status_code == 200:
        print("{}: {}".format(message['status'], message['uri']))

        obj['external_documents'].append({
            'title': "Special Collections @ DU",
            'location': row[1]
        })

        obj['instances'].append({
            'instance_type': "digital_object",
            'jsonmodel_type': "instance",
            'is_representative': True,
            'digital_object': { 'ref': message['uri'] }
        })

        post_json(uri, obj)
    else:
        print("Error: {}".format(message['error']))
        pass


def search_for(obj):
    r = AS.client.get('/repositories/2/search', params={'q': obj, 'type[]': "archival_object", 'page': "1"})
    if r.status_code == 200:
        results = json.loads(r.text)['results']
        uris = [r for r in results if r['component_id'] == obj and 'pui' not in r['types']]
        if len(uris) == 0:
            print("No URI found: {}".format(row[0]))
            pass
        elif len(uris) == 1:
            return uris[0]['uri']
        else:
            print("Found multiple URIs for {}".format(row[0]))
            pass
    else:
        r.raise_for_status()


if args.file:
    if os.path.exists(args.file):
        with open(args.file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                obj = get_json(row[0])
                # here is where you would do your edits
                post_json(row[0], obj)
    else:
        print("File not found: {}".format(args.file))
else:
    print("Please provide a file")
