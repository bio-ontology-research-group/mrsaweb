from django.urls import path, include
from mrsaweb.apps.uploader.views import SyncMetadataRDF

urlpatterns = [
    # path('upload/', include('uploader.api_urls')),
    path('upload/<col_id>/metadata', SyncMetadataRDF.as_view()),
]
