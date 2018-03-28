#!/usr/bin/env python

import json, configparser, requests

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

agent_types = ['people', 'corporate_entities', 'families']
local = ["local","prov","tucua","built"]
uri_prefix = {
  'aat': "http://vocab.getty.edu/aat/",
  'lcgft': "http://id.loc.gov/authorities/genreForms",
  'lcnaf': "http://id.loc.gov/authorities/names/",
  'lcsh': "http://id.loc.gov/authorities/subjects/",
  'lcshg': "http://id.loc.gov/authorities/subjects/",
  'tgm': "http://id.loc.gov/vocabulary/graphicMaterials/",
  'tgn': "http://vocab.getty.edu/tgn",
  'viaf': "http://viaf.org/viaf/"
}

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

def post_object(url,agent,max_retries=10,timeout=5):
    retry_on_exceptions = (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError
    )
    for i in range(max_retries):
        try:
            post = requests.post(url,headers=headers,data=json.dumps(agent))
        except retry_on_exceptions:
            print("Connection failed. Retry in five seconds... ")
            continue
        else:
            if(post.status_code == requests.codes.ok):
                print("Updated authority ID for %s" % url)
            else:
                error = post.json()
                print("Error: %s" % error['error'])
            break

ids = requests.get(("%s/subjects?all_ids=true" % resourceURL),headers=headers).json()
for val in ids:
    url = "%s/subjects/%d" % (resourceURL, val)
    subj = get_object(url).json()
    if('source' in subj and subj['source'] not in local and 'authority_id' in subj and subj['authority_id'].startswith(uri_prefix[subj['source']])):
        new_id = subj['authority_id'].replace(uri_prefix[subj['source']], '')
        subj['authority_id'] = new_id
        post_object(url, subj)
