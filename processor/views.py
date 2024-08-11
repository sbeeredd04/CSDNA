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

    if not os.path.exists(csv_file_path):
        with open(csv_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Image', 'Label'])

    with open(csv_file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        labeled_images_data = list(reader)
        labeled_images = [row[0] for row in labeled_images_data][1:]

    images = [f for f in os.listdir(os.path.join(settings.MEDIA_ROOT)) if f.startswith('group_') and f.endswith('.png')]
    images.sort()

    remaining_images = [img for img in images if img not in labeled_images]
    current_image = remaining_images[0] if remaining_images else None

    if request.method == 'POST' and current_image:
        label = request.POST.get('label', '')  # Get the dynamic label
        with open(csv_file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_image, label])

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
import csv
import os
from django.http import HttpResponse
from django.conf import settings
from io import BytesIO

def generate_pie_chart(request):
    csv_file_path = os.path.join(settings.MEDIA_ROOT, 'image_labels.csv')
    
    if os.path.exists(csv_file_path):
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            data = list(reader)
            total_images = len(data)
            csdna_images = sum(1 for row in data if row['Label'] == '1')
            other_images = total_images - csdna_images
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
            
            
            # Set the style for the plots
            plt.style.use('dark_background')
            plt.rcParams.update({
                "text.color": "white",
                "axes.edgecolor": "white",
                "axes.labelcolor": "white",
                "xtick.color": "white",
                "ytick.color": "white",
                "axes.facecolor": "none",  # Transparent face
                "figure.facecolor": "none"  # Transparent figure
            })
            
            # Data for pie chart
            pie_labels = ['CSDNA', 'Others']
            pie_sizes = [csdna_images, other_images]
            pie_colors = ['#ca6abd','#55A8E6']
            pie_explode = (0.1, 0)  # explode 1st slice
            
            # Data for histogram
            hist_labels = ['CSDNA', 'Others']
            hist_sizes = [csdna_images, other_images]
            hist_colors = ['#ca6abd','#55A8E6']

            # Creating subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

            # Plotting pie chart
            ax1.pie(pie_sizes, explode=pie_explode, labels=pie_labels, colors=pie_colors, autopct=lambda p: f'{p:.1f}%\n({p*sum(pie_sizes)/100 :.0f})', shadow=True, startangle=90, textprops={'color':'white'})
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.


            # Plotting histogram
            ax2.bar(hist_labels, hist_sizes, color=hist_colors)

            # Adding the count above the bars in histogram
            for i in range(len(hist_sizes)):
                ax2.text(i, hist_sizes[i] + max(hist_sizes)*0.01, str(hist_sizes[i]), ha='center', color='white')

            # Setting labels for histogram
            ax2.set_ylabel('Number of Images')
            ax2.set_title('Distribution of Images')
            
            padding_amount = 2
            
            # Set y limit for padding above the bars
            ax2.set_ylim(0, max(hist_sizes) + padding_amount)
            #set x limit for padding on the sides
            ax2.set_xlim(-0.5, len(hist_labels)-1 + 0.5)

            
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.8, hspace=0.8)
            
            # Save it to a temporary buffer.
            buf = BytesIO()
            plt.savefig(buf, format='png', transparent=True)  # Set transparent to True here
            # Embed the result in the html output.
            data = buf.getvalue()

            plt.close(fig)  # Close the figure after saving to buffer

            # Send buffer in a http response the the browser with the mime type image/png set
            return HttpResponse(data, content_type='image/png')
    else:
        return HttpResponse("No data available to generate charts.", content_type='text/plain')
    
    @csrf_exempt
    def update_category_count(request):
        if request.method == 'POST':
            data = json.loads(request.body)
            category = data.get('category')
            count = data.get('count')
            # Update the count in your model or session, as needed
            # Example:
            # Category.objects.filter(key=category).update(count=count)
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'failed'}, status=400)
