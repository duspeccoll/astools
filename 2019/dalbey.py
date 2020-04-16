#!/usr/bin/env python

################
#
# dalbey.py -- normalize Fridlyand Archive metadata enough that I can work with it in OpenRefine
#
################

import json
from lxml import etree

namespaces = {'mods': 'http://www.loc.gov/mods/v3'}


def parse_title(xml):
    titleInfo = xml.find("mods:titleInfo", namespaces=namespaces)
    if titleInfo is not None:
        title = titleInfo.find("mods:title", namespaces=namespaces).text
        subtitle = titleInfo.find("mods:subTitle", namespaces=namespaces)
        if subtitle is not None:
            title += " ({})".format(subtitle.text)
    return title


def parse_dates(xml):
    dates = []
    if record.xpath("mods:originInfo/mods:dateCreated", namespaces=namespaces) is not None:
        for date in record.xpath("mods:originInfo/mods:dateCreated", namespaces=namespaces):
            dates.append({
                'expression': date.text,
                'type': "single"
            })
    return dates


def parse_extents(xml):
    extent = xml.find("mods:physicalDescription", namespaces=namespaces)
    if extent is not None:
        ext = {}

        container_summary = extent.find("mods:extent", namespaces=namespaces)
        if container_summary is not None:
            ext['container_summary'] = container_summary.text

        return [ext]
    else:
        return []


def parse_notes(xml):
    notes = []

    # abstract
    abstract = xml.find("mods:abstract", namespaces=namespaces)
    if abstract is not None:
        notes.append({
            "type": "abstract",
            "content": [abstract.text]
        })

    # materialspec
    materialspec = xml.find("mods:physicalDescription/mods:note[@type='physical details']", namespaces=namespaces)
    if materialspec is not None:
        notes.append({
            'type': "materialspec",
            'content': [materialspec.text]
        })

    # physdesc
    physdesc = xml.find("mods:physicalDescription/mods:note[@type='physical description']", namespaces=namespaces)
    if physdesc is not None:
        notes.append({
            'type': "physdesc",
            'content': [physdesc.text]
        })

    # physloc
    physloc = xml.find("mods:location/mods:physicalLocation", namespaces=namespaces)
    if physloc is not None:
        notes.append({
            "type": "physloc",
            "content": [record.find("mods:location/mods:physicalLocation", namespaces=namespaces).text]
        })

    # odd
    odds = xml.xpath("mods:note", namespaces=namespaces)
    if odds is not None:
        for odd in odds:
            if odd.xpath("@lang")[0] == 'eng':
                label = "English note"
            elif odd.xpath("@lang")[0] == 'rus':
                label = "Russian note"
            notes.append({
                'type': "odd",
                'label': label,
                'subnotes': [{
                    'content': odd.text
                }]
            })

    # relatedmaterial
    relatedmaterials = xml.xpath("mods:relatedItem/mods:identifier", namespaces=namespaces)
    subnotes = []
    if relatedmaterials is not None:
        note = {"type": "relatedmaterial"}

        for relatedmaterial in relatedmaterials:
            subnotes.append(relatedmaterial.text)

        if len(subnotes) > 0:
            note['subnotes'] = ", ".join(subnotes)
            notes.append(note)

    # userestrict
    userestrict = xml.find("mods:accessCondition[@type='useAndReproduction']", namespaces=namespaces)
    if userestrict is not None:
        notes.append({
            "type": "userestrict",
            "subnotes": [{
                "content": userestrict.text
            }]
        })

    return notes


def parse_subjects(xml):
    subjects = []
    form = xml.find("mods:form", namespaces=namespaces)
    if form is not None:
        subjects.append({'term': form.text, 'type': "genre_form"})

    terms = xml.xpath("mods:subject", namespaces=namespaces)
    if terms is not None:
        for term in terms:
            for topic in term.xpath("./mods:topic", namespaces=namespaces):
                subjects.append({'term': topic.text, 'type': "topical"})
            for geographic in term.xpath("./mods:geographic", namespaces=namespaces):
                subjects.append({'term': geographic.text, 'type': "geographic"})

    return subjects


def parse_linked_agents(xml):
    linked_agents = []
    subjects = xml.xpath("mods:subject/mods:name/mods:namePart", namespaces=namespaces)
    if subjects is not None:
        for subject in subjects:
            linked_agents.append({'term': subject.text, 'role': "subject"})

    creators = xml.xpath("mods:name[./mods:role/mods:roleTerm = 'creator']", namespaces=namespaces)
    if creators is not None:
        for creator in creators:
            linked_agents.append({'term': creator.find("mods:namePart", namespaces=namespaces).text, 'role': "creator"})

    return linked_agents


def parse_documents(xml):
    if xml.find("mods:location/mods:url", namespaces=namespaces) is not None:
        return [{
            'title': "Special Collections @ DU",
            'location': xml.find("mods:location/mods:url", namespaces=namespaces).text
        }]
    else:
        return []


parser = etree.XMLParser(remove_blank_text=True)
object = {}
archival_objects = []

with open('dalbey.xml', 'r') as xml:
    root = etree.parse(xml, parser).getroot()
    records = root.xpath("mods:mods", namespaces=namespaces)
    for record in records:
        archival_objects.append({
            'title': parse_title(record),
            'component_id': record.find("mods:identifier", namespaces=namespaces).text,
            'dates': parse_dates(record),
            'extents': parse_extents(record),
            'notes': parse_notes(record),
            'linked_agents': parse_linked_agents(record),
            'subjects': parse_subjects(record),
            'external_documents': parse_documents(record)
        })

object['archival_objects'] = archival_objects
with open('dalbey.json', 'w') as f:
    json.dump(object, f)
