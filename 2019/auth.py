#!/usr/bin/env python

# This script just logs you into your ArchivesSpace backend and prints a session ID.
# You can copy it into whatever script you want to write to do useful things with your database.

import configparser, requests

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

print(session)
