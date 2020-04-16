#!/usr/bin/env python

import configparser, requests, time

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

modified_since = config.get('Timestamps', 'marc_export')
post = requests.post(repositoryBaseURL + "/marc_export?modified_since=" + modified_since,headers=headers)
post.encoding = 'utf8'

if(post.status_code == requests.codes.ok):
    filename = config.get('Destinations', 'home') + "/marc_export_" + time.strftime("%Y%m%d_%H%M%S") + ".xml"
    f = open(filename, 'w', encoding='utf8')
    f.write(post.text)
    f.close()

    # set the current time as the new timestamp in your config file
    config['Timestamps']['marc_export'] = str(int(time.time()))
    with open('local_settings.cfg', 'w') as cf:
        config.write(cf)
else:
    print(post.text)
