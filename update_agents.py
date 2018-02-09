#!/usr/bin/env python

import json, ConfigParser, requests

config = ConfigParser.ConfigParser()
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

uri_prefix = {
  'nad': "http://id.loc.gov/authorities/names/",
  'naf': "http://id.loc.gov/authorities/names/",
  'ulan': "http://vocab.getty.edu/ulan/",
  'lcsh': "http://id.loc.gov/authorities/subjects/",
  'viaf': "http://viaf.org/viaf/"
}

for agent_type in agent_types:
	ids = requests.get(resourceURL + "/agents/" + agent_type + "?all_ids=true",headers=headers).json()
	for n in ids:
		loc = ["local", "ingest", "prov"]
		agent = requests.get(resourceURL + "/agents/" + agent_type + "/" + str(n)).json()
		names = agent['names']
		for name in names:
			if name['authorized'] is True:
				if ('source' in name and name['source'] not in loc and 'authority_id' in name and name['authority_id'].startswith(uri_prefix[name['source']])):
					new_id = name['authority_id'].replace(uri_prefix[name['source']], '')
					name['authority_id'] = new_id
					post = requests.post(resourceURL + "/agents/" + agent_type + "/" + str(n),headers=headers,data=json.dumps(agent))
					if(post.status_code == requests.codes.ok):
						print "Replaced URL prefix for " + agent['title']
					else:
						print post.text
