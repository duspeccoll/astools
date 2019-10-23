#!/usr/bin/env python

##########
#
# kaltura_bulk_upload.py -- uses the Kaltura Work Order plugin to build Bulk Upload XML
#
# Requires a CSV file of URIs as input; will then create an mrss/channel XML object,
# add the 'item' tree for the Kaltura XML for each URI in the CSV file, and save the
# resulting XML object at 'kaltura.xml' in the directory where this script lives
#
##########

import argparse
import csv
import json
import os
from lxml import etree
from asnake.aspace import ASpace

ap = argparse.ArgumentParser(description='Add or update ArchivesSpace metadata properties from CSV input')
ap.add_argument('-f', '--file', help='The CSV file containing the metadata to add')
args = ap.parse_args()

AS = ASpace()

nsmap = {'xsd': "http://www.w3.org/2001/XMLSchema", 'xsi': "http://www.w3.org/2001/XMLSchema-instance"}
attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "noNamespaceSchemaLocation")


if args.file:
    if os.path.exists(args.file):
        thumbnail = input("Thumbnail URL (leave blank for none): ")
        root = etree.Element("mrss", {attr_qname: "ingestion.xsd"}, nsmap=nsmap)
        channel = etree.SubElement(root, "channel")
        with open(args.file, 'r') as uris:
            reader = csv.reader(uris)
            for row in reader:
                print("downloading {}".format(row[0]))
                r = AS.client.get("{}/kaltura.xml".format(row[0]))
                if r.status_code == 200:
                    xml = etree.fromstring(r.text.encode('utf-8'))
                    item = xml.find("channel/item")
                    if thumbnail:
                        tns = etree.Element("thumbnails")
                        tn = etree.SubElement(tns, "thumbnail", attrib={'isDefault': 'true'})
                        url = etree.SubElement(tn, "urlContentResource", attrib={'url': thumbnail})
                        item.find("contentAssets").addnext(tns)
                    channel.append(item)
                else:
                    error = json.loads(r.text)['error']
                    print("Error: {}: {}".format(error, row[0]))
        kxml = etree.ElementTree(root)
        with open('kaltura.xml', 'w') as f:
            f.write(etree.tostring(kxml, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8"))
            print("Bulk upload file written to kaltura.xml")
    else:
        print("File not found: {}".format(args.file))
else:
    print("Please provide a file")
