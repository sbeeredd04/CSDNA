from django.urls import path
from .views import image_upload_view, label_image_view
from .views import download_labeled_data_view
from .views import all_labeled_view
from .views import image_result_view
from .views import download_labeled_group_images_view
from .views import generate_pie_chart

urlpatterns = [
    path('', image_upload_view, name='image-upload'),
    path('label/', label_image_view, name='label-image'),  # Changed from 'label_image' to 'label-image'
    path('download-labeled-data/', download_labeled_data_view, name='download-labeled-data'),
    path('all-labeled/', all_labeled_view, name='all_labeled'),
    path('image-result/', image_result_view, name='image-result'), # Add this line with the correct view function
    path('download-labeled-group-images/', download_labeled_group_images_view, name='download-labeled-group-images'),
    path('generate-pie-chart/', generate_pie_chart, name='generate-pie-chart'),
]
