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
    if 'labeled_images' not in request.session:
        request.session['labeled_images'] = []

    labeled_images = request.session['labeled_images']

    # Filter out the labeled images
    group_images_paths = [
        img_path for img_path in os.listdir(settings.MEDIA_ROOT)
        if img_path.startswith("group") and img_path not in labeled_images
    ]

    if request.method == "POST":
        image_path = request.POST.get("image_path")
        label = request.POST.get("label")
        relative_path = os.path.relpath(image_path, settings.MEDIA_ROOT)

        # Save the labeled data to the database
        LabeledImage.objects.create(image_path=relative_path, label=label)

        # Add the labeled image to the session to avoid labeling again
        labeled_images.append(image_path)
        request.session.modified = True

        # If there are more images to label, continue to the next one
        if group_images_paths:
            # Remove the labeled image from the list for the next iteration
            group_images_paths.remove(image_path)

    if group_images_paths:
        # Proceed to label the next image
        image_path = group_images_paths[0]
        fs = FileSystemStorage()
        image_url = fs.url(image_path)
        context = {'image_path': image_path, 'image_url': image_url}
        return render(request, 'processor/label_image.html', context)
    else:
        # If no images are left to label, redirect to the completion view
        return HttpResponseRedirect(reverse('all_labeled'))



def download_labeled_data_view(request):
    # Path to the CSV file
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'labeled_images.csv')
    
    print("\n")
    print("csv_file_path: ", csv_file_path)
    print("\n")
    
    # Gather all labeled images
    labeled_images = LabeledImage.objects.all()

    # Prepare CSV data
    csv_data = "image_path,label\n"
    for image in labeled_images:
        csv_data += f"{image.image_path},{image.label}\n"

    # Create a response with a CSV file
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="labeled_images.csv"'

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