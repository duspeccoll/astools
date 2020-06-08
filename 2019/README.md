# University of Denver ArchivesSpace Python scripts

What's here:

* **auth.py:** basic authentication script; used as the basis for authenticating against the ArchivesSpace backend for all of the other scripts here
* **marc_export.py:** works with our [MARC Export](https://github.com/duspeccoll/marc_export) plugin to download MARCXML representations of all Resources created or updated after a given time
* **update_agents.py:** updates authority IDs for Agents to remove the namespace prefix (which we infer from their source)
* **update_component_ids.py:** does a find/replace on the component ID for all Archival Objects in a Resource tree (ID provided by the user)
