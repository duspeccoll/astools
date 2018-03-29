#!/usr/bin/env python

# This script just logs you into your ArchivesSpace backend and prints a session ID.
# You can copy it into whatever script you want to write to do useful things with your database.

import configparser, requests, json, os, sys

config = configparser.ConfigParser()
config.read('local_settings.cfg')

dictionary = {
  'baseURL': config.get('ArchivesSpace', 'baseURL'),
  'repository':config.get('ArchivesSpace', 'repository'),
  'user': config.get('ArchivesSpace', 'user'),
  'password': config.get('ArchivesSpace', 'password')
}

repositoryBaseURL = '{baseURL}/repositories/{repository}'.format(**dictionary)
resourceURL = '{baseURL}'.format(**dictionary)

auth = requests.post('{baseURL}/users/{user}/login?password={password}&expiring=false'.format(**dictionary)).json()
session = auth['session']
headers = {'X-ArchivesSpace-Session': session}

data_models = { "1": "resources", "2": "archival_objects", "3": "agents", "4": "subjects", "5": "digital_objects", "6": "accessions", "7": "top_containers", "8": "container_profiles", "9": "events" }
agent_types = ["people", "corporate_entities", "families", "software"]

class Printer():
    def __init__(self, data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush

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
            print("Connection lost. Retry in five seconds... ")
            continue
        else:
            return result

def string_from_dict(msg, d):
    print(msg)
    for k in sorted(d):
        print('* (' + k + ') ' + d[k])
    s = input('> ')
    if s in d:
        return d[s]
    else:
        print("Please enter a value from the list.")
        string_from_dict(msg, d)

def run_report(jsonmodel):
    request_url = "/%s" % jsonmodel
    if jsonmodel == "subjects" or jsonmodel == "container_profiles" or jsonmodel.startswith("agents"):
        request_url = resourceURL + request_url
    else:
        request_url = repositoryBaseURL + request_url

    ids = get_object(request_url + "?all_ids=true").json()
    jsonmodel = jsonmodel.replace('agents/', '')
    file_out = config.get('Destinations', 'home') + "/%s_report.json" % jsonmodel
    f = open(file_out, "w")
    f.write("{\"" + jsonmodel + "\":[")
    for idx, val in enumerate(ids,start=1):
        output = "Writing %s (%d of %d)... " % (jsonmodel, idx, len(ids))
        Printer(output)
        json = get_object("%s/%d" % (request_url, val))
        f.write(json.text.rstrip())
        if idx < len(ids):
            f.write(",")
    f.write("]}")
    f.close()
    print("done!")

jsonmodel = string_from_dict('Please select a data model:', data_models)

if jsonmodel == "agents":
    for atype in agent_types:
        agent_type = "agents/" + atype
        run_report(agent_type)
else:
    run_report(jsonmodel)
