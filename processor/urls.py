# processor/urls.py

from django.urls import path
from .views import image_upload_view

urlpatterns = [
    path('', image_upload_view, name='image-upload'),  # This line should not have 'upload/' prefix
]
