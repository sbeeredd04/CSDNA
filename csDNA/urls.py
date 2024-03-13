from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from processor.views import landing_page, download_zip

urlpatterns = [
    path('', landing_page, name='landing-page'),
    path('upload/', include('processor.urls')),  # Include processor's URLs with 'upload/' prefix
    path('download/<str:zip_file>/', download_zip, name='download-zip'),
    # Remove the line with 'label/', include('processor.urls')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
