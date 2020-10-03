from django.conf import settings
from django.http import HttpResponseRedirect
from urllib import parse

import logging
import requests

logger = logging.getLogger(__name__)

HTTP_PROT = 'http://'
VIRTUOSO_HOST = getattr(settings, 'VIRTUOSO_HOST')
VIRTUOSO_SPARQL_PORT = getattr(settings, 'VIRTUOSO_SPARQL_PORT')
SPARQL_ENDPOINT_URL = HTTP_PROT + VIRTUOSO_HOST + ":" + str(VIRTUOSO_SPARQL_PORT) + "/sparql"

def execute_sparql(query, format):
    query_url="{endpoint}?query={query}&format={format}&timeout=0&debug=on&run={run}" \
                .format(
                    endpoint=SPARQL_ENDPOINT_URL, 
                    query=parse.quote(query), 
                    format=parse.quote(format), 
                    run=parse.quote('Run Query'))
    response = requests.get(query_url)
    return response
