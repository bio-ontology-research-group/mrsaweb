import urllib
import logging

from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404

from django.views.generic import CreateView, DetailView, ListView
from django.conf import settings

from .forms import UploadForm
from mrsaweb.mixins import FormRequestMixin
from mrsaweb.virtuoso import insert
from uploader.models import Upload
from .utils import api
from .utils import fix_iri_path_param
from .submissions import Submissions
from rdflib import Graph

from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

class UploadCreateView(FormRequestMixin, CreateView):

    model = Upload
    form_class = UploadForm
    template_name = 'uploader/form.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UploadCreateView, self).get_context_data(*args, **kwargs)
        return context

    def form_valid(self, form):
        return super().form_valid(form)
    
    def get_success_url(self, *args, **kwargs):
        return reverse('uploader-view', kwargs={'pk': self.object.pk})


class UploadDetailView(DetailView):
    model = Upload
    template_name = 'uploader/view.html'

class UploadListView(ListView):
    model = Upload
    template_name = 'uploader/list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(col_uuid__isnull=False)
        user = self.request.user
        if user:
            queryset = queryset.filter(user=user)
        else:
            queryset = queryset.filter(user__isnull=True)
        return queryset.order_by('-pk')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context

def submission_list_view(request):
    service = Submissions()

    page = request.GET.get('page') or 1
    page = int(page)

    try:
        pageSize = 20
        offset = 1
        if page > 1:
            offset = pageSize * (page - 1)

        submissions = service.find(limit=pageSize, offset=offset)
        current_page = submissions[:-1]
        num_pages = int((int(submissions[-1]['total']['value']) / pageSize)+ 1)
        has_next = True if num_pages > page else False
        has_previous = True if 1 < page else False
        next_page_number = page + 1
        previous_page_number = page - 1
        page_range = range(1,num_pages + 1)
        current_page = service.resolve_references(current_page)

    except InvalidPage as e:
        raise Http404(str(e))

    context = {
        'current_page': current_page,
        'number': page,
        'num_pages': num_pages,
        'has_next': has_next,
        'has_previous': has_previous,
        'previous_page_number': previous_page_number,
        'next_page_number': next_page_number,
        'page_range': page_range
    }
    return render(request, 'uploader/list-submission.html', context)

def submission_details_view(request, iri):
    iri = fix_iri_path_param(iri)
    service = Submissions()
    submission = service.get_by_iri(iri)
    submission = service.resolve_references([submission])[0]

    context = { 'submission': submission }

    return render(request, 'uploader/view-submission.html', context)


class SyncMetadataRDF(APIView):
    """
    Sync's metadata with triple store 
    """

    def post(self, request, col_id, format=None):
        try:
            res_uri = settings.ARVADOS_COL_BASE_URI + col_id + "/metadata.rdf"
            g = Graph()
            g.parse(res_uri)
            insert(g)
            return Response()
        except Exception as e:
            logger.exception("message")