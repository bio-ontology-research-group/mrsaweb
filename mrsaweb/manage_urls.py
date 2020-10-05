from django.urls import path, include

urlpatterns = [
    path('upload/', include('uploader.manage_urls')),
]
