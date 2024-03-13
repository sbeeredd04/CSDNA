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


def label_image_view(request):
    # Define the path for the CSV file where labels are stored
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    
    # Ensure the CSV file exists and has the appropriate headers
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Image', 'Label'])  # Header

    # Load the list of images
    images = [img for img in os.listdir(settings.MEDIA_ROOT) if img.endswith(('jpg', 'jpeg', 'png'))]
    
    # Sort the images to ensure consistent order
    images.sort()

    # Attempt to retrieve the current image index from the session
    current_index = request.session.get('current_image_index', 0)

    # If the form has been submitted
    if request.method == 'POST':
        label = request.POST.get('label', 'No')
        
        # Write the label to the CSV file
        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([images[current_index], label])

        # Move to the next image
        current_index += 1
        request.session['current_image_index'] = current_index

        # If all images have been labeled, redirect to a completion view
        if current_index >= len(images):
            return HttpResponseRedirect(reverse('all_labeled'))

    # If there are still images to be labeled
    if current_index < len(images):
        image_path = images[current_index]
        context = {
            'image_path': image_path,
            'image_url': os.path.join(settings.MEDIA_URL, image_path)
        }
        return render(request, 'processor/label_image.html', context)

    # If no more images to label, redirect to completion
    return HttpResponseRedirect(reverse('all_labeled'))





def download_labeled_data_view(request):
    # Path to the CSV file you want to save
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'labeled_images.csv')
    
    # Make sure the directory exists
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    # Gather all labeled images
    labeled_images = LabeledImage.objects.all()

    # Open the file to write or overwrite as needed ('w' mode)
    with open(csv_file_path, 'w', newline='') as csvfile:
        # CSV writer object
        csvwriter = csv.writer(csvfile)
        # Write the header
        csvwriter.writerow(["image_path", "label"])
        # Write each labeled image data
        for image in labeled_images:
            csvwriter.writerow([image.image_path, image.label])
    
    # After saving the file, you can read it back to send in the response
    with open(csv_file_path, 'rb') as csvfile:
        response = HttpResponse(csvfile.read(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(csv_file_path)}"'

    return response



def all_labeled_view(request):
    return render(request, 'processor/labeling_complete.html')


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