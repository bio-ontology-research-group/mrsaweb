from django.urls import include, path
from django.contrib.auth.decorators import login_required
from mrsaweb.apps.sparql.views import sparql_form_view, sparql_view, SparqlExamples

urlpatterns = [
    path('', sparql_form_view, name='sparql-isparql'),
    path('endpoint', sparql_view, name='sparql-endpoint'),
    path('examples', SparqlExamples.as_view(), name='sparql-examples')
]
