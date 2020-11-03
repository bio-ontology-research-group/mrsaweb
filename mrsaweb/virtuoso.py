from django.conf import settings
from django.http import HttpResponseRedirect
from urllib import parse

import logging
import requests
import shutil
import subprocess
import uuid

logger = logging.getLogger(__name__)

HTTP_PROT = 'http://'
VIRTUOSO_HOST = getattr(settings, 'VIRTUOSO_HOST')
VIRTUOSO_SPARQL_PORT = getattr(settings, 'VIRTUOSO_SPARQL_PORT')
VIRTUOSO_USER = getattr(settings, 'VIRTUOSO_USER')
VIRTUOSO_PWD = getattr(settings, 'VIRTUOSO_PWD')
RDF_GRAPH_URI = getattr(settings, 'RDF_GRAPH_URI')
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

def insert(graph):
    try:
        f = "entry.rdf"
        graph.serialize(f, format="pretty-xml")
        curd_endpoint = SPARQL_ENDPOINT_URL + "-graph-crud-auth?graph-uri=" + RDF_GRAPH_URI
        CMD = "time curl --digest --user " + VIRTUOSO_USER + ":" + VIRTUOSO_PWD + " --verbose -X POST \
            --url " + curd_endpoint + " \
            --upload-file '" + str(f) + "' \
            --write-out '%{url_effective};%{http_code};%{time_total};%{time_namelookup};%{time_connect};%{size_download};%{speed_download}\\n' \
            && echo `date +%Y-%m-%d.%H%M.%S.%N` Processing file '" + f + "' completed with exit status:$e_status at `date +%Y-%m-%d.%H%Mhrs:%S.%N`;"
        print("command:", CMD)
        process = subprocess.Popen(CMD, stdout=subprocess.PIPE, text=True, shell=True)
        for line in process.stdout:
            print(line.strip())
        
    except Exception as e:
        logger.exception("message")