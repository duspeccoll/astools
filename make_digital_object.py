#!/usr/bin/env python

# What this script does:
# 1. logs into the ArchivesSpace backend via the ArchivesSnake library (you will need to configure that before you
# run the script)
# 2. accepts a digital object package constructed according to the Digital Repository ingest specification as input
# 3. checks to see if uri.txt exists and generates it if it does not
#    (check_uri_txt)
# 4. checks to see if a digital object has been attached to the item record matching the provided component ID,
# and creates it if it does not
#    (check_digital_object)
# 5. processes each file and attaches a digital object component to the digital object containing that file's name,
# format, and size in bytes
#    (process_files)

import argparse
import csv
import json
import magic
import os
import sys
import os.path

from asnake.aspace import ASpace

DEFAULT_URL = r"http://as02.coalliance.org:8080"
TESTING_URL = r"http://as0222.coalliance.org:8080/"

AS = None
VERBOSE_LOG = False


class DigitalObjectException(Exception):
    def __init__(self, message):
        super(DigitalObjectException, self).__init__()
        self.message = message


def get_json(uri):
    r = AS.client.get(uri)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        r.raise_for_status()


def post_json(uri, data):
    r = AS.client.post(uri, json=data)
    message = json.loads(r.text)
    if r.status_code == 200:
        if VERBOSE_LOG:
            if 'uri' in message:
                as_log("{}: {}".format(message['status'], message['uri']))
            else:
                as_log("{}: {}".format(message['status'], uri))
    else:
        as_log("Error: {}".format(message['error']))


def magic_to_as(file_format_name):
    # translate libmagic's file format enumeration labels to archivesspace
    if file_format_name == "x-wav":
        file_format_name = "wav"
    elif file_format_name == "quicktime":
        file_format_name = "mov"
    elif file_format_name == "mpeg":
        file_format_name = "mp3"
    elif file_format_name == "x-font-gdos":
        file_format_name = "mp3"
    elif file_format_name == "vnd.adobe.photoshop":
        file_format_name = "tiff"
    return file_format_name


# process the files in the path and add digital object components where necessary for each file
def process_files(ref, path, no_kaltura_id, no_caption, no_publish):
    print("Fetching digital object tree... ")
    tree = get_json("{}/tree/root".format(ref))

    print("Checking files... ")
    files = [f for f in sorted(os.listdir(path), key=lambda a: a) if os.path.isfile(os.path.join(path, f)) and
             f != "uri.txt" and f != "Thumbs.db"]
    if files:
        for file in files:
            path_to_file = os.path.join(path, file)
            file_format_name = magic.from_file(path_to_file, mime=True).split("/")[-1]
            # ignore file size if it won't fit in an int(11) to bypass mysql db constraints
            if os.path.getsize(path_to_file) < 2147483647:
                file_size_bytes = os.path.getsize(path_to_file)
            else:
                file_size_bytes = ''

            file_format_name = magic_to_as(file_format_name)
            #file_format_name = "tiff"

            make_new = True

            if tree["child_count"] > 0:
                tree_files = [child for child in tree["precomputed_waypoints"][""]['0'] if child['title'] == file]
                print("Checking for file-level metadata updates... ")
                for child in tree_files:
                    make_new = False
                    record = get_json(child['uri'])
                    updates = False

                    if 'component_id' not in record:
                        if not no_kaltura_id:
                            kaltura_id = input("> Kaltura ID (leave blank for none): ")
                            if kaltura_id:
                                record['component_id'] = kaltura_id
                                updates = True

                    if record['file_versions']:
                        version = record['file_versions'][0]
                        if 'file_uri' not in version or version['file_uri'] != file:
                            record['file_versions'][0]['file_uri'] = file
                            updates = True
                        if 'file_format_name' not in version or version['file_format_name'] != file_format_name:
                            record['file_versions'][0]['file_format_name'] = file_format_name
                            updates = True
                        if 'file_size_bytes' not in version or version['file_size_bytes'] != file_size_bytes:
                            record['file_versions'][0]['file_size_bytes'] = file_size_bytes
                            updates = True
                    else:
                        record['file_versions'].append({
                            'jsonmodel_type': "file_version",
                            'file_uri': file,
                            'file_format_name': file_format_name,
                            'file_size_bytes': file_size_bytes,
                            'is_representative': True,
                        })
                        updates = True

                    if not no_caption:
                        caption = input("> Caption (leave blank for none): ")
                        if caption:
                            if 'caption' in record['file_versions'][0]:
                                if record['file_versions'][0]['caption'] != caption:
                                    record['file_versions'][0]['caption'] = caption
                                    updates = True
                            else:
                                record['file_versions'][0]['caption'] = caption
                                updates = True

                    if no_publish:
                        record["publish"] = False
                        record['file_versions'][0]["publish"] = False

                    if updates:
                        print("Updating {}... ".format(file))
                        record['digital_object'] = {'ref': ref}
                        post_json(child['uri'], record)
                    else:
                        print("No updates to make")
            if make_new:
                print("Adding file-level metadata to ArchivesSpace... ")
                data = {
                    'jsonmodel_type': "digital_record_children",
                    'children': [{
                        'title': file,
                        'publish': True,
                        'file_versions': [{
                            'jsonmodel_type': "file_version",
                            'file_uri': file,
                            'publish': True,
                            'file_format_name': file_format_name,
                            'file_size_bytes': file_size_bytes,
                            'is_representative': True
                        }],
                        'digital_object': {'ref': ref}
                    }]
                }
                if not no_kaltura_id:
                    kaltura_id = input("> Kaltura ID (leave blank for none): ")
                    if kaltura_id:
                        data['children'][0]['component_id'] = kaltura_id
                if not no_caption:
                    caption = input("> Caption (leave blank for none): ")
                    if caption:
                        data['children'][0]['file_versions'][0]['caption'] = caption
                if no_publish:
                    data['children'][0]['publish'] = False
                    data['children'][0]['file_versions'][0]['publish'] = False
                post_json("{}/children".format(ref), data)
    else:
        print("No files found.")


# create a digital object and attach it to the provided item record
def write_digital_object(item):
    as_log("Creating digital object... ")
    obj = {'title': item['display_string'], 'jsonmodel_type': "digital_object"}

    links = [d for d in item['external_documents'] if d['title'] == "Special Collections @ DU"]
    if links:
        if len(links) > 1:
            raise DigitalObjectException("There shouldn't be more than one repository link on an item record.")
        else:
            obj['digital_object_id'] = links[0]['location']
    else:
        obj['digital_object_id'] = item['component_id']

    # post the digital object and link its reference URI to the provided item record
    r = AS.client.post('/repositories/2/digital_objects', json=obj)
    if r.status_code == 200:
        ref = json.loads(r.text)['uri']
        item['instances'].append({
            'instance_type': "digital_object",
            'jsonmodel_type': "instance",
            'is_representative': True,
            'digital_object': {'ref': ref}
        })
        post_json(item['uri'], item)

        return ref
    else:
        sys.exit("Error: {}".format(json.loads(r.text)['error']))


# given a URI from uri.txt, download the item record and check that it is cataloged according to the digital object
# metadata specification
def check_digital_object(uri):
    as_log("Downloading item... ")
    item = get_json(uri)

    as_log("Checking for digital object... ")
    instances = [i for i in item['instances'] if i['instance_type'] == "digital_object"]

    if instances:
        # script exits if the item has more than one digital object attached to it
        if len(instances) > 1:
            raise DigitalObjectException(
                "An item cannot have more than one digital object. Please check ArchivesSpace to confirm your "
                "item is cataloged properly.")
        else:
            ref = instances[0]['digital_object']['ref']
            objects = [i for i in instances if i['is_representative']]
            if not objects:
                as_log("Making the digital object representative... ")
                for instance in item['instances']:
                    if instance['digital_object']['ref'] == ref:
                        instance['is_representative'] = True
                post_json(item['uri'], item)
    else:
        ref = write_digital_object(item)

    return ref


# write uri.txt by searching for the component ID specified in the directory name and fetching its URI
def write_uri_txt(component_id, path):
    global AS
    resp = AS.client.get('/repositories/2/search', params={'q': component_id, 'type[]': "archival_object", 'page': "1"})
    if resp.status_code == 200:
        results = json.loads(resp.text)['results']
        uris = [r for r in results if r['component_id'] == component_id and 'pui' not in r['types']]

        # script exits if there are no results or if more than one archival_object has the provided call number
        if not uris:
            raise DigitalObjectException("Couldn't find this item in ArchivesSpace. Has it been cataloged? Is the "
                                         "call number accurate?")
        if len(uris) > 1:
            raise DigitalObjectException("Multiple objects with this call number found. Check ArchivesSpace for more "
                                         "information.")

        uri = uris[0]['uri']
        if os.path.exists(path):
            os.remove(path)
        as_log("Writing uri.txt... ")
        with open(path, 'w') as f:
            f.write(uri)

        return uri
    else:
        resp.raise_for_status()


# confirm that uri.txt exists and that its URI matches the object (based on the call number provided in the directory
# name)
def check_uri_txt(path):
    component_id = os.path.basename(path)
    uri_txt = "{}/uri.txt".format(path)
    as_log("Checking for uri.txt... ")

    if os.path.exists(uri_txt):
        as_log("Checking if URI matches item record... ")
        with open(uri_txt, 'r') as f:
            uri = f.read().replace('\n', '')
            item = get_json(uri)
            if item['component_id'] != component_id:
                uri = write_uri_txt(component_id, uri_txt)
    else:
        uri = write_uri_txt(component_id, uri_txt)
    return uri


# get the digital object's relative path from the user
def get_path(path=None):
    if path:
        return os.path.join(r"../digital_object_workspace/", path)
    else:
        raise Exception
        while True:
            path = os.path.join(r"../digital_object_workspace/", input('Path to your digital object: '))
            if path:
                if not os.path.exists(path):
                    sys.exit("{} does not exist".format(path))
                if not os.path.isdir(path):
                    sys.exit("{} is not a directory".format(path))
                return path
            else:
                print("Please enter a path")


def as_log(message):
    print(message)


def process(path, no_kaltura_id, no_caption, no_publish):
    uri = check_uri_txt(path)
    ref = check_digital_object(uri)
    process_files(ref, path, no_kaltura_id, no_caption, no_publish)


def main():
    global AS

    parser = argparse.ArgumentParser(description='Make a digital object based on the contents of a directory')
    parser.add_argument('-u', '--user', help="ArchivesSpace username")
    parser.add_argument('-p', '--password', help="ArchivesSpace password")
    parser.add_argument('path', help="The directory to process")
    parser.add_argument('-b', '--batch', action='store_true', help="A CSV file containing a list of directories to process in a batch")
    parser.add_argument('--no_kaltura-id', help="Do not prompt the user to provide Kaltura IDs", action='store_true')
    parser.add_argument('--no_caption', help="Do not prompt the user to provide captions", action='store_true')
    parser.add_argument('--no_publish', help="Do not publish digital object component", action='store_true')
    parser.add_argument('--test', help="Run on test ArchivesSpace server.", action='store_true')

    args = parser.parse_args()

    if args.test:
        AS = ASpace(baseurl=TESTING_URL, username=args.user, password=args.password)
    else:
        AS = ASpace(baseurl=DEFAULT_URL, username=args.user, password=args.password)

    no_kaltura_id = args.no_kaltura_id
    no_caption = args.no_caption
    no_publish = args.no_publish
    if args.batch:
        for f in sorted(os.scandir(get_path(args.path)), key=lambda a: a.name):
            if f.is_dir():
                path = f.path
                print("CURRENT ITEM: " + f.name)
                process(path, no_kaltura_id, no_caption, no_publish)
    else:
        print("CURRENT ITEM: " + args.path)
        path = get_path(args.path)
        process(path, no_kaltura_id, no_caption, no_publish)


if __name__ == "__main__":
    try:
        main()
    except DigitalObjectException as e:
        sys.exit(e.message)
