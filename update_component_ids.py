#!/usr/bin/env python

# This script takes as input the ID of the Resource whose component IDs you want to update, the string to replace, and the
# replacement string.
#
# You could use this as the basis for other batch find/replace processes if you wanted.

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

def getString(message):
	s = input(message)
	if s:
		return s
	else:
		print("This field is required.")
		getString(message)

def processChildren(child, old, new):
	ao = requests.get(resourceURL + child['record_uri'],headers=headers).json()
	if('component_id' in ao and old in ao['component_id']):
		new_id = ao['component_id'].replace(old, new)
		ao['component_id'] = new_id
		post = requests.post(resourceURL + child['record_uri'],headers=headers,data=json.dumps(ao))
		if(post.status_code == requests.codes.ok):
			print("Replaced component ID:" + ao['component_id'])
		else:
			print(post.text)
	children = child['children']
	for record in children:
		processChildren(record, old, new)

resourceID = getString("Enter the resource ID to update: ")
old = getString("Enter the string to replace: ")
new = getString("Enter the replacement string: ")

tree = requests.get(repositoryBaseURL + "/resources/" + resourceID + "/tree",headers=headers).json()
children = tree['children']
for child in children:
	processChildren(child, old, new)
