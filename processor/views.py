import os
from django.http import HttpResponse, Http404
from django.shortcuts import render
from .forms import ImageUploadForm, ImageProcessingOptionsForm
from .models import ImageUpload
from .image_processing import process_images  # Ensure this handles both single and multiple images correctly
from django.conf import settings
from zipfile import ZipFile
from .models import LabeledImage
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.urls import reverse
import shutil
from django.core.files.storage import FileSystemStorage
import csv

def image_upload_view(request):
    
    clear_media_directory()
    
    context = {
        'image_form': ImageUploadForm(),
        'options_form': ImageProcessingOptionsForm(),
    }
    
    if request.method == 'POST':
        image_form = ImageUploadForm(request.POST, request.FILES)
        options_form = ImageProcessingOptionsForm(request.POST)
        if image_form.is_valid() and options_form.is_valid():
            obj = image_form.save()
            group_radius = options_form.cleaned_data.get('group_radius')
            min_dots = options_form.cleaned_data.get('min_dots')
            threshold = options_form.cleaned_data.get('threshold')
            circle_color = options_form.cleaned_data.get('circle_color')
            circle_width = options_form.cleaned_data.get('circle_width')

            full_images_zip_filename, groups_zip_filename, full_image_path, group_images_paths = process_images(
                obj.image.path, group_radius, min_dots, threshold, circle_color, circle_width
            )

            context = {
                'full_image_path': full_image_path,  # This should be the path of the full image with circles
                'group_images_paths': group_images_paths,  # This should be a list of paths for group images
                'full_images_zip': full_images_zip_filename,  # This should be the filename of the zip with full images
                'groups_zip': groups_zip_filename,  # This should be the filename of the zip with group images
            }

            # Return to the same view with updated context
            return render(request, 'processor/image_result.html', context)
            
    return render(request, 'processor/image_upload.html', context)

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


from django.shortcuts import render, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
import os
import csv

def label_image_view(request):
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    
    # Ensure the CSV file exists with the appropriate headers
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Image', 'Label'])  # Write the header

    # Load the list of image filenames and their labels from the CSV file
    with open(csv_file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        labeled_images_data = list(reader)
        labeled_images = [row[0] for row in labeled_images_data][1:]  # Exclude header

    # Load and sort the list of image files in the media directory and only look for /media/group_{i}.png
    images = [f for f in os.listdir(os.path.join(settings.MEDIA_ROOT)) if f.startswith('group_') and f.endswith('.png')]
    images.sort()

    # Determine the next image to label
    remaining_images = [img for img in images if img not in labeled_images]
    current_image = remaining_images[0] if remaining_images else None

    if request.method == 'POST' and current_image:
        label = request.POST.get('label', '0')
        # Write the label to the CSV file
        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_image, label])

        # Redirect to refresh and move to the next image
        return HttpResponseRedirect(reverse('label-image'))

    analyzed_images = len(images) - len(remaining_images)
    total_images = len(images)
    progress = (analyzed_images / total_images) * 100 if total_images > 0 else 0

    context = {
        'image_path': current_image,
        'image_url': os.path.join(settings.MEDIA_URL, current_image) if current_image else None,
        'remaining_images': len(remaining_images),
        'total_images': len(images),
        'analyzed_images': analyzed_images,
        'progress': progress,
    }

    return render(request, 'processor/label_image.html', context)




def download_labeled_data_view(request):
    # Specify the path to the CSV file that contains the labels
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    
    # Check if the file exists before attempting to download
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(csv_file_path)}"'
            return response
    else:
        # Handle the case where the file does not exist
        response = HttpResponse("No labeled data available for download.", content_type='text/plain')
        return response




def all_labeled_view(request):
    return render(request, 'processor/labeling_complete.html')

def image_result_view(request):
    return render(request, 'processor/image_result.html')

def clear_media_directory():
    # Path to the media directory
    media_dir_path = settings.MEDIA_ROOT

    # Remove the entire directory
    if os.path.isdir(media_dir_path):
        shutil.rmtree(media_dir_path)
        print(f"Deleted the media directory: {media_dir_path}")
        print("\n")
        
    #checking if media directory is deleted
    if not os.path.isdir(media_dir_path):
        print(f"Media directory is deleted: {media_dir_path}")
        print("\n")
    else:
        print(f"Media directory is not deleted: {media_dir_path}")
        print("\n")