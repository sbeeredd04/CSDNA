import os
from django.http import HttpResponse, Http404
from django.shortcuts import render
from .forms import ImageUploadForm
from .models import ImageUpload
from .image_processing import process_image
from django.conf import settings
from zipfile import ZipFile

def image_upload_view(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            full_image_path, group_images_paths = process_image(obj.image.path)
            
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
        form = ImageUploadForm()
    return render(request, 'processor/image_upload.html', {'form': form})

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
