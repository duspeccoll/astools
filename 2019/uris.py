#!/usr/bin/env python

###############################################################################
#
# uris.py -- generate uri.txt files
#
# The Special Collections @ DU ingest process requires a uri.txt file
# alongside the digital object files, so that the repository knows from which
# ArchivesSpace record it should be pulling metadata.
#
# This script iterates over a list of folders in a directory (provided by the
# user), searching for the call number in the folder's title and writing the
# URI it finds to that folder's uri.txt file.
#
###############################################################################

import json, os
from asnake.aspace import ASpace

AS = ASpace()
repo = AS.repositories(2)

def get_path():
    path = input('Path to the folder containing your objects: ')
    if not os.path.isdir(path):
        raise ValueError("Not a directory: {}".format(path))
    return path


# this is a bit janky, but the search API returns frontend *and* PUI results,
# so we need to filter out the PUI results for de-duplication
def search_for(object):
    r = AS.client.get('/repositories/2/search', params={'q': object, 'type[]': "archival_object", 'page': "1"})
    if r.status_code == 200:
        results = json.loads(r.text)['results']
        return [r for r in results if r['component_id'] == object and 'pui' not in r['types']]
    else:
        r.raise_for_status()


path = get_path()
for dir in os.listdir(path):
    if os.path.isdir(os.path.join(path, dir)):
        results = search_for(dir)
        if len(results) == 0:
            print("No URI found: {}".format(dir))
        elif len(results) == 1:
            print("Writing {} to {}/uri.txt".format(results[0]['uri'], os.path.join(path, dir)))
            with open("{}/uri.txt".format(os.path.join(path, dir)), 'w') as f:
                f.write(results[0]['uri'])
        else:
            print("Found multiple URIs for {}".format(dir))
    else:
        print("Not a directory: {}".format(dir))
