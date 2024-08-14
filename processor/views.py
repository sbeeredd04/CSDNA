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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.db.models import F
from .models import Category

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
            num_categories = options_form.cleaned_data.get('num_categories')  # Capture number of categories

            # Store num_categories in session
            request.session['num_categories'] = num_categories
            print(f"Stored {num_categories} categories in session.")  # Debugging

            full_images_zip_filename, groups_zip_filename, full_image_path, group_images_paths = process_images(
                obj.image.path, group_radius, min_dots, threshold, circle_color, circle_width
            )

            context = {
                'full_image_path': full_image_path,
                'group_images_paths': group_images_paths,
                'full_images_zip': full_images_zip_filename,
                'groups_zip': groups_zip_filename,
            }

            return render(request, 'processor/image_result.html', context)

    return render(request, 'processor/image_upload.html', context)


import os
from django.conf import settings
def label_image_view(request):
    # Ensure the media directory exists
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)

    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')

    # Initialize the CSV file if it doesn't exist
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Image', 'Label'])

    num_categories = request.session.get('num_categories', 1)  # Default to 1 if not set
    categories_range = range(1, int(num_categories) + 1)

    images = [f for f in os.listdir(os.path.join(settings.MEDIA_ROOT)) if f.startswith('group_') and f.endswith('.png')]
    images.sort()

    # Read the CSV file to get the list of already labeled images and their counts
    labeled_images_data = []
    category_counts = {str(i): 0 for i in categories_range}  # Initialize category counts
    
    with open(csv_file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        labeled_images_data = list(reader)[1:]  # Skipping the header row

    labeled_images = [row[0] for row in labeled_images_data]  # List of already labeled images

    # Count the occurrences of each label to update the category counts
    for row in labeled_images_data:
        label = row[1]
        if label in category_counts:
            category_counts[label] += 1
    
    remaining_images = [img for img in images if img not in labeled_images]
    current_image = remaining_images[0] if remaining_images else None

    if request.method == 'POST' and current_image:
        print(f"POST data received: {request.POST}")  # Debugging
        
        # Get the selected label from POST data
        label = request.POST.get('label', '')

        if not label:
            print("Label not found in POST data.")  # Debugging
        else:
            print(f"Label received: {label}")  # Debugging

            # Append the label to the CSV file
            with open(csv_file_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([current_image, label])
            
            print(f"Labeled image {current_image} with {label}")  # Debugging

            # Update the category count in the dictionary
            if label in category_counts:
                category_counts[label] += 1

        # Redirect to refresh the view with the next image
        return HttpResponseRedirect(reverse('label-image'))

    # Update the category counts in the database
    for label, count in category_counts.items():
        category_obj, created = Category.objects.get_or_create(key=label)
        category_obj.count = count
        category_obj.save()
        print(f"Category {label} - Updated Count in DB: {category_obj.count}")  # Debugging

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
    'category_counts': {str(key): value for key, value in category_counts.items()},  # Ensure keys are strings
    'categories_range': categories_range,  # Pass the categories range to the context
    }

    return render(request, 'processor/label_image.html', context)



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
    num_categories = request.session.get('num_categories', 1)
    categories_range = range(1, int(num_categories) + 1)
    
    print(f"Number of categories: {num_categories}")  # Debugging
    print(f"Categories range: {list(categories_range)}")  # Debugging
    
    return render(request, 'processor/labeling_complete.html', {
        'categories_range': categories_range,
    })


def image_result_view(request):
    return render(request, 'processor/image_result.html')

def clear_media_directory():
    # Path to the media directory
    media_dir_path = settings.MEDIA_ROOT

    # Remove the entire directory
    if os.path.isdir(media_dir_path):
        shutil.rmtree(media_dir_path)
        
# views.py

def download_labeled_group_images_view(request):
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    
    if os.path.exists(csv_file_path):
        # Read the CSV and filter out the rows where the label is '1'
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            labeled_images = [row['Image'] for row in reader if row['Label'] == '1']

        # Create a zip file with all the images labeled '1'
        zip_filename = "labeled_group_images.zip"
        zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_filename)
        
        with ZipFile(zip_file_path, 'w') as zip_file:
            for image_filename in labeled_images:
                image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
                if os.path.exists(image_path):
                    zip_file.write(image_path, arcname=image_filename)
        
        # Serve the zip file
        with open(zip_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={zip_filename}'
            return response

    raise Http404("No labeled group images available for download.")


#method to get the number of images with label 1 vs total images and displaying the piechart
def labeled_images_piechart(request):
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    
    if os.path.exists(csv_file_path):
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            labeled_images = [row['Image'] for row in reader if row['Label'] == '1']
            total_images = len([row['Image'] for row in reader])
            remaining_images = total_images - len(labeled_images)
            print(f"Total images: {total_images}")
            print(f"Labeled images: {len(labeled_images)}")
            print(f"Remaining images: {remaining_images}")
            print("\n")
            
            #pie chart
            import matplotlib.pyplot as plt
            labels = 'Labeled Images', 'Remaining Images'
            sizes = [len(labeled_images), remaining_images]
            colors = ['gold', 'yellowgreen']
            explode = (0.1, 0)  # explode 1st slice
            plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
            plt.axis('equal')
            plt.savefig('media/pie_chart.png')
            plt.show()
            
            return render(request, 'processor/piechart.html')
    else:
        raise Http404("No labeled group images available for download.")
    

import matplotlib.pyplot as plt
import os
from django.http import HttpResponse
from io import BytesIO
from .models import Category

def generate_pie_chart(request):
    # Fetch category counts from the database
    categories = Category.objects.all()
    category_labels = [cat.key for cat in categories]
    category_sizes = [cat.count for cat in categories]

    # Creating the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # Pie chart for category distribution
    ax1.pie(
        category_sizes, 
        labels=category_labels, 
        autopct=lambda p: f'{p:.1f}%\n({p*sum(category_sizes)/100 :.0f})',
        colors=['#ca6abd', '#55A8E6', '#ffcc5c', '#96ceb4', '#ffeead'], 
        shadow=True, 
        startangle=90, 
        explode=[0] * len(category_labels),  # No exploding slices
        textprops={'color':'white', 'fontsize': 16}  # Increase text size here
    )
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.set_title('Category Distribution', color='white', fontsize=20)  # Increase title font size

    # Histogram for category counts
    ax2.bar(
        category_labels, 
        category_sizes, 
        color=['#ca6abd', '#55A8E6', '#ffcc5c', '#96ceb4', '#ffeead']
    )

    # Adding the count above the bars in the histogram
    for i in range(len(category_sizes)):
        ax2.text(i, category_sizes[i] + max(category_sizes) * 0.02, str(category_sizes[i]), 
                 ha='center', color='white', fontsize=16)  # Increase text size here

    ax2.set_xlabel('Categories', color='white', fontsize=16)  # Increase label font size
    ax2.set_ylabel('Number of Images', color='white', fontsize=16)  # Increase label font size
    ax2.set_title('Image Count per Category', color='white', fontsize=20)  # Increase title font size
    ax2.set_facecolor('none')

    # Dynamically adjust the y-axis to fit the data
    ax2.set_ylim(0, max(category_sizes) + max(category_sizes) * 0.2)

    # Adjusting the layout
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.8, hspace=0.8)
    
    # Save it to a temporary buffer.
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)  # Set transparent to True here
    buf.seek(0)

    plt.close(fig)  # Close the figure after saving to buffer

    # Send buffer in an HTTP response to the browser with the mime type image/png set
    return HttpResponse(buf.getvalue(), content_type='image/png')


from django.http import HttpResponse, Http404
from django.conf import settings
import os
from zipfile import ZipFile
import csv

def download_images_by_category_view(request, category_label):
    print(f"Attempting to download images for category: {category_label}")  # Debugging

    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    print(f"Looking for CSV file at: {csv_file_path}")  # Debugging
    
    if os.path.exists(csv_file_path):
        print("CSV file found. Reading the file...")  # Debugging

        # Read the CSV and filter out the rows where the label matches the category
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            labeled_images = [row['Image'] for row in reader if row['Label'] == str(category_label)]

        print(f"Found {len(labeled_images)} images for category {category_label}")  # Debugging

        if not labeled_images:
            print(f"No images found for category {category_label}.")  # Debugging
            raise Http404(f"No images found for category {category_label}.")

        # Create a zip file with all the images matching the category label
        zip_filename = f"category_{category_label}_images.zip"
        zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_filename)
        print(f"Creating zip file at: {zip_file_path}")  # Debugging
        
        with ZipFile(zip_file_path, 'w') as zip_file:
            for image_filename in labeled_images:
                image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
                if os.path.exists(image_path):
                    print(f"Adding image {image_filename} to zip file.")  # Debugging
                    zip_file.write(image_path, arcname=image_filename)
                else:
                    print(f"Image {image_filename} not found at {image_path}. Skipping...")  # Debugging
        
        print("Zip file creation complete.")  # Debugging

        # Serve the zip file
        with open(zip_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={zip_filename}'
            print(f"Serving zip file: {zip_filename}")  # Debugging
            return response

    print("CSV file not found or no images for the specified category.")  # Debugging
    raise Http404(f"No images found for category {category_label}.")