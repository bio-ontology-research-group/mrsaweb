from django.conf import settings
from urllib import parse

import logging
import requests

logger = logging.getLogger(__name__)

ABEROWL_API_URL = getattr(settings, 'ABEROWL_API_URL')

def find_by_iri(iri_dict):
    resolved_dict = {}
    for item in iri_dict:
        ontology = item['ontology']
        iri = item['iri']
        query_url=f"{ABEROWL_API_URL}/ontology/{ontology}/class/{iri}"
        response = requests.get(query_url)
        result = response.json()
        if len(result['result']) > 0:
            resolved_dict[result['result'][0]['class']] = result['result'][0]
    return resolved_dict
