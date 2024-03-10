import os
from django.http import HttpResponse, Http404
from django.shortcuts import render
from .forms import ImageUploadForm, ImageProcessingOptionsForm  # Make sure to import the new form
from .models import ImageUpload
from .image_processing import process_image
from django.conf import settings
from zipfile import ZipFile

def image_upload_view(request):
    if request.method == 'POST':
        image_form = ImageUploadForm(request.POST, request.FILES)
        options_form = ImageProcessingOptionsForm(request.POST)  # Instantiate the options form
        if image_form.is_valid() and options_form.is_valid():
            obj = image_form.save()
            # Extract options data from the form
            group_radius = options_form.cleaned_data.get('group_radius')
            min_dots = options_form.cleaned_data.get('min_dots')
            threshold = options_form.cleaned_data.get('threshold')
            circle_color = options_form.cleaned_data.get('circle_color')
            circle_width = options_form.cleaned_data.get('circle_width')

            # Pass the options to the process_image function
            full_image_path, group_images_paths = process_image(
                obj.image.path, group_radius, min_dots, threshold, circle_color, circle_width
            )
            
            # Create a zip file
            zip_filename = "group_images.zip"
            s3_zip_path = os.path.join(settings.MEDIA_ROOT, zip_filename)
            with ZipFile(s3_zip_path, 'w') as zip_file:
                for image_path in group_images_paths:
                    image_full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                    zip_file.write(image_full_path, os.path.basename(image_full_path))
            
            context = {
                'full_image_path': full_image_path,
                'zip_file': zip_filename,  # Pass the zip filename to the template
            }
            return render(request, 'processor/image_result.html', context)
    else:
        image_form = ImageUploadForm()
        options_form = ImageProcessingOptionsForm()  # Instantiate the options form for GET request
    return render(request, 'processor/image_upload.html', {
        'image_form': image_form,
        'options_form': options_form  # Include the options form in the context
    })

def landing_page(request):
    return render(request, 'processor/landing_page.html')

def download_zip(request, zip_file):
    zip_path = os.path.join(settings.MEDIA_ROOT, zip_file)
    if os.path.exists(zip_path):
        with open(zip_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_path)}"'
            return response
    raise Http404
