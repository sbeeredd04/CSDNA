# At the project level (csDNA/urls.py)

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from processor.views import landing_page, download_zip

urlpatterns = [
    path('', landing_page, name='landing-page'),
    path('upload/', include('processor.urls')),
    path('download/<str:zip_file>/', download_zip, name='download-zip'),
    # ... other url patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
