#!/usr/bin/env python

import argparse, csv, json, magic, os, sys
from asnake.aspace import ASpace


AS = ASpace()


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
        if 'uri' in message:
            print("{}: {}".format(message['status'], message['uri']))
        else:
            print("{}: {}".format(message['status'], uri))
    else:
        print("Error: {}".format(message['error']))


# process the files in the path and add digital object components where necessary for each file
def process_files(ref, path):
    print("Fetching digital object tree... ")
    tree = get_json("{}/tree".format(ref))

    print("Checking files... ")
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f != "uri.txt"]
    if files:
        for file in files:
            print("\nProcessing {}... ".format(file))
            path_to_file = os.path.join(path, file)
            file_format_name = magic.from_file(path_to_file, mime=True).split("/")[-1]
            file_size_bytes = os.path.getsize(path_to_file)

            tree_files = [child for child in tree['children'] if child['title'] == file]
            if tree_files:
                print("Checking for file-level metadata updates... ")
                for child in tree['children']:
                    if child['title'] == file:
                        record = get_json(child['record_uri'])
                        updates = False

                        if 'component_id' not in record:
                            if not args.no_kaltura_id:
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

                        if not args.no_caption:
                            caption = input("> Caption (leave blank for none): ")
                            if caption:
                                if 'caption' in record['file_versions'][0]:
                                    if record['file_versions'][0]['caption'] != caption:
                                        record['file_versions'][0]['caption'] = caption
                                        updates = True
                                else:
                                    record['file_versions'][0]['caption'] = caption
                                    updates = True

                        if updates:
                            print("Updating {}... ".format(file))
                            record['digital_object'] = {'ref': ref}
                            post_json(child['record_uri'], record)
                        else:
                            print("No updates to make")
            else:
                print("Adding file-level metadata to ArchivesSpace... ")
                data = {
                    'jsonmodel_type': "digital_record_children",
                    'children': [{
                        'title': file,
                        'file_versions': [{
                            'jsonmodel_type': "file_version",
                            'file_uri': file,
                            'file_format_name': magic.from_file(path_to_file, mime=True).split("/")[-1],
                            'file_size_bytes': os.path.getsize(path_to_file),
                            'is_representative': True
                        }],
                        'digital_object': {'ref': ref}
                    }]
                }
                if not args.no_kaltura_id:
                    kaltura_id = input("> Kaltura ID (leave blank for none): ")
                    if kaltura_id:
                        data['children'][0]['component_id'] = kaltura_id
                if not args.no_caption:
                    caption = input("> Caption (leave blank for none): ")
                    if caption:
                        data['children'][0]['file_versions'][0]['caption'] = caption
                post_json("{}/children".format(ref), data)
    else:
        print("No files found.")


# create a digital object and attach it to the provided item record
def write_digital_object(item):
    print("Creating digital object... ")
    obj = {'title': item['display_string'], 'jsonmodel_type': "digital_object"}

    links = [d for d in item['external_documents'] if d['title'] == "Special Collections @ DU"]
    if links:
        if len(links) > 1:
            sys.exit("There shouldn't be more than one repository link on an item record.")
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
    print("Downloading item... ")
    item = get_json(uri)

    print("Checking for digital object... ")
    instances = [i for i in item['instances'] if i['instance_type'] == "digital_object"]

    if instances:
        # script exits if the item has more than one digital object attached to it
        if len(instances) > 1:
            sys.exit("An item cannot have more than one digital object. Please check ArchivesSpace to confirm your "
                     "item is cataloged properly.")
        else:
            ref = instances[0]['digital_object']['ref']
            objects = [i for i in instances if i['is_representative']]
            if not objects:
                print("Making the digital object representative... ")
                for instance in item['instances']:
                    if instance['digital_object']['ref'] == ref:
                        instance['is_representative'] = True
                post_json(item['uri'], item)
    else:
        ref = write_digital_object(item)

    return ref


# write uri.txt by searching for the component ID specified in the directory name and fetching its URI
def write_uri_txt(id, path):
    print("Writing uri.txt... ")
    r = AS.client.get('/repositories/2/search', params={'q': id, 'type[]': "archival_object", 'page': "1"})
    if r.status_code == 200:
        results = json.loads(r.text)['results']
        uris = [r for r in results if r['component_id'] == id and 'pui' not in r['types']]

        # script exits if there are no results or if more than one archival_object has the provided call number
        if not uris:
            sys.exit("Couldn't find this item in ArchivesSpace. Has it been cataloged? Is the call number accurate?")
        if len(uris) > 1:
            sys.exit("Multiple objects with this call number found. Check ArchivesSpace for more information.")

        uri = uris[0]['uri']
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'w') as f:
            f.write(uri)

        return uri
    else:
        r.raise_for_status()


# confirm that uri.txt exists and that its URI matches the object (based on the call number provided in the directory
# name)
def check_uri_txt(path):
    component_id = path.split("/")[-1]
    uri_txt = "{}/uri.txt".format(path)
    print("Checking for uri.txt... ")

    if os.path.exists(uri_txt):
        print("Checking if URI matches item record... ")
        with open(uri_txt, 'r') as f:
            uri = f.read().replace('\n','')
            item = get_json(uri)
            if item['component_id'] != component_id:
                uri = write_uri_txt(component_id, uri_txt)
    else:
        uri = write_uri_txt(component_id, uri_txt)
    return uri


# get the digital object's relative path from the user
def get_path(path=None):
    if path:
        return path
    else:
        while True:
            path = input('Path to your digital object: ')
            if path:
                if not os.path.exists(path):
                    sys.exit("{} does not exist".format(path))
                if not os.path.isdir(path):
                    sys.exit("{} is not a directory".format(path))
                return path
            else:
                print("Please enter a path")


def main():
    parser = argparse.ArgumentParser(description='Make a digital object based on the contents of a directory')
    parser.add_argument('-p', '--path', help="The directory to process")
    parser.add_argument('--no-kaltura-id', help="Do not prompt the user to provide Kaltura IDs", action='store_true')
    parser.add_argument('--no-caption', help="Do not prompt the user to provide captions", action='store_true')
    
    args = parser.parse_args()
    path = get_path(args.path)
    uri = check_uri_txt(path)
    ref = check_digital_object(uri)
    process_files(ref, path)


if __name__ == "__main__":
    main()
