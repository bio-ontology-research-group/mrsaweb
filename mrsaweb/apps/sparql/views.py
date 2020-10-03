import urllib
import logging
import requests
import json

from mrsaweb.apps.sparql.example import LIST_SUBMISSION_EXAMPLE, LIST_SARS_COV_SUBMISSION_EXAMPLE, GET_SUBMISSION_BY_URI_EXAMPLE
from mrsaweb.apps.sparql.forms import SparqlForm
from django.shortcuts import render 
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response


logger = logging.getLogger(__name__)

HTTP_PROT = 'http://'
VIRTUOSO_HOST = getattr(settings, 'VIRTUOSO_HOST')
VIRTUOSO_SPARQL_PORT = getattr(settings, 'VIRTUOSO_SPARQL_PORT')
SPARQL_ENDPOINT_URL = HTTP_PROT + VIRTUOSO_HOST + ":" + str(VIRTUOSO_SPARQL_PORT) + "/sparql"


def sparql_form_view(request): 

    context = {'listSubmissionExample' : LIST_SUBMISSION_EXAMPLE}
    form = SparqlForm(request.GET or None) 
    context['form']= form 
    
    return render(request, "form.html", context)


def sparql_view(request): 

    form = SparqlForm(request.GET or None) 
    
    if form and form.is_valid():
        query_str = urllib.parse.urlencode(request.GET, doseq=True)
        
        query_url=f"{SPARQL_ENDPOINT_URL}?{query_str}"
        logger.debug("redirect to:" + query_url)
        response = requests.get(query_url)

        django_response = HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers['Content-Type']
        )
        return django_response
    else:
        return HttpResponse({'status': 'error', 'message': 'invalid form'})


class SparqlExamples(APIView):

    def get(self, request, format=None):
        try:
            examples = {
                'listSubmission': LIST_SUBMISSION_EXAMPLE,
                'listSarsCovSubmission': LIST_SARS_COV_SUBMISSION_EXAMPLE,
                'getSubmissionByUri': GET_SUBMISSION_BY_URI_EXAMPLE
            }
            return Response(json.dumps(examples))
        except Exception as e:
            logger.exception("message")