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

# We wanted to strip the URI prefixes from authorized name forms for our agents so we could construct them dynamically using the provided name source. So that's what this does:

agent_types = ['people', 'corporate_entities', 'families']
local = ["local", "ingest", "prov"]
uri_prefix = {
  'nad': "http://id.loc.gov/authorities/names/",
  'naf': "http://id.loc.gov/authorities/names/",
  'ulan': "http://vocab.getty.edu/ulan/",
  'lcsh': "http://id.loc.gov/authorities/subjects/",
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
            result = requests.get(url,headers=headers).json()
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
                print("Updated authority ID for " + url)
            else:
                error = post.json()
                print("Error: " + error['error'])
            break

for agent_type in agent_types:
    url = "%s/agents/%s?all_ids=true" % (resourceURL, agent_type)
    ids = requests.get(url,headers=headers).json()
    for val in ids:
        url = "%s/agents/%s/%d" % (resourceURL, agent_type, val)
        agent = get_object(url)
        names = agent['names']
        for name in names:
            if name['authorized'] is True:
                if('source' in name and name['source'] not in local and 'authority_id' in name and name['authority_id'].startswith(uri_prefix[name['source']])):
                    new_id = name['authority_id'].replace(uri_prefix[name['source']], '')
                    name['authority_id'] = new_id
                    post_object(url,agent)
