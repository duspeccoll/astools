#!/usr/bin/env python

# this only works on subjects but it would be rad if it worked on any data model you want

import json, configparser, requests, argparse, os

# let configparser get our local settings
config = configparser.ConfigParser()
config.read('local_settings.cfg')
dictionary = {
  'baseURL': config.get('ArchivesSpace', 'baseURL'),
  'repository':config.get('ArchivesSpace', 'repository'),
  'user': config.get('ArchivesSpace', 'user'),
  'password': config.get('ArchivesSpace', 'password'),
  'path': config.get('Destinations', 'home')
}

# let argparse set up arguments for passing a file to it
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="A file of URIs to pass to ArchivesSpace")
args = parser.parse_args()

# set up ArchivesSpace backend URLs
repositoryBaseURL = '{baseURL}/repositories/{repository}'.format(**dictionary)
resourceURL = '{baseURL}'.format(**dictionary)
path = '{path}'.format(**dictionary)

# get a backend session
auth = requests.post('{baseURL}/users/{user}/login?password={password}&expiring=false'.format(**dictionary)).json()
session = auth['session']
headers = {'X-ArchivesSpace-Session': session}

# get an object from the API
def get_object(url,max_retries=10,timeout=5):
    retry_on_exceptions = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError
    )
    for i in range(max_retries):
        try:
            result = requests.get(url,headers=headers)
        except retry_on_exceptions:
            print("Connection failed. Retry in five seconds... ")
            continue
        else:
            return result

# post a revised object to the API
def post_object(url,obj,log,max_retries=10,timeout=5):
    retry_on_exceptions = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError
    )
    f = open(log, 'a')
    for i in range(max_retries):
        try:
            post = requests.post(url,headers=headers,data=json.dumps(obj))
        except retry_on_exceptions:
            print("Connection failed. Retry in five seconds... ")
            continue
        else:
            if(post.status_code == requests.codes.ok):
                print("%s updated" % url)
                f.write("%s updated\n" % url)
            else:
                error = post.json()
                print("Error while processing %s: %s" % (url, error['error']))
                f.write("Error while processing %s: %s\n" % (url, error['error']))
            break

    f.close()

# actually do whatever find/replace operation you want to do
def process_object(obj):
    # do whatever you need to do here...

    # ...then return the processed object to the script
    return obj

log = "%s/logfile.txt" % path
try:
    os.remove(log)
except OSError:
    pass

# if a file of URIs is provided, work on that file; otherwise work on all subjects
if args.file:
    f = open(args.file, "r")
    for uri in f:
        url = "%s%s" % (resourceURL, uri.rstrip())
        subj = get_object(url).json()
        subj = process_object(subj)
        post_object(url, subj, log)
else:
    ids = requests.get(("%s/subjects?all_ids=true" % resourceURL),headers=headers).json()
    for val in ids:
        url = "%s/subjects/%d" % (resourceURL, val)
        subj = get_object(url).json()
        subj = process_object(subj)
        post_object(url, subj, log)

print("Script done and results written to %s" % log)
