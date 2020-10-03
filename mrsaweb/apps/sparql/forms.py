from django import forms
from django.utils.translation import ugettext_lazy as _
from mrsaweb.apps.sparql.example import LIST_SUBMISSION_EXAMPLE
    
class SparqlForm(forms.Form):
    query = forms.CharField(label=_('Query'), widget=forms.Textarea, initial=LIST_SUBMISSION_EXAMPLE)
    query.input = True

    options = [
        ('text/html', 'HTML'),
        ('application/sparql-results+xml','XML'),
        ('application/sparql-results+json','JSON'),
        ('application/javascript','Javascript'),
        ('text/turtle','Turtle'),
        ('application/rdf+xml','RDF/XML'),
        ('text/plain','N-Triples'),
        ('text/csv','CSV'),
        ('text/tab-separated-values','TSV')
    ]
    format = forms.TypedChoiceField(label=_('Result Format'), choices= options, initial='text/html')
    format.input = True
    
    debug =  forms.BooleanField(label=_('Strict check'), required=False, initial=True)
    debug.input = False
    log_debug_info = forms.BooleanField(label=_('Log debug info'), required=False)
    log_debug_info.input = False
    explain = forms.BooleanField(label=_('SPARQL compilation report only'), required=False)
    explain.input = False

    def input(self):
        return filter(lambda x: x.input == True, self.fields.values())

    def check(self):
        return filter(lambda x: x.input == False, self.fields.values())

