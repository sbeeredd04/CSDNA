from PIL import Image, ImageDraw
import numpy as np
import os
from django.conf import settings
from zipfile import ZipFile
from sklearn.cluster import DBSCAN
import glob

def process_images(input_path, group_radius=50, min_dots=100, threshold=60, circle_color='green', circle_width=8):
    # If the input path is a directory, find all image files in the directory
    if os.path.isdir(input_path):
        image_paths = glob.glob(os.path.join(input_path, '*.png'))  # Adjust the pattern if needed
    else:  # Single image file
        image_paths = [input_path]
    
    full_images_paths = []
    all_groups_paths = []

    # Process each image
    for image_path in image_paths:
        # Load the image
        original_image = Image.open(image_path)
        image_array = np.array(original_image)

        # Find all dots: assuming that the dots are the only non-black pixels
        dots = np.where(np.all(image_array > threshold, axis=-1))
        dot_coordinates = np.array(list(zip(dots[1], dots[0])))

        # Perform DBSCAN clustering
        db = DBSCAN(eps=group_radius, min_samples=6).fit(dot_coordinates)

        # Get labels and unique cluster identifiers
        labels = db.labels_
        unique_labels = set(labels)

        # Initialize a dictionary to store grouped dots
        grouped_dots = {label: [] for label in unique_labels if label != -1}

        # Group dots based on cluster labels
        for label, dot in zip(labels, dot_coordinates):
            if label != -1:
                grouped_dots[label].append(dot)

        images_paths = []
        # Save individual groups without circles but with enough space for circles
        for idx, group in enumerate(grouped_dots.values()):
            if len(group) >= min_dots:
                xs, ys = zip(*group)
                min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
                
                # Include the space for the radius in the bounding box
                bounding_box = [
                    max(min_x - group_radius, 0),
                    max(min_y - group_radius, 0),
                    min(max_x + group_radius, original_image.width),
                    min(max_y + group_radius, original_image.height)
                ]

                cropped_image = original_image.crop(bounding_box)
                group_image_path = f"group_{idx}.png"
                cropped_image.save(os.path.join(settings.MEDIA_ROOT, group_image_path))
                images_paths.append(group_image_path)

        # Save the full image with circles for reference (optional)
        image_with_circles = original_image.copy()
        draw = ImageDraw.Draw(image_with_circles)
        for group in grouped_dots.values():
            if len(group) >= min_dots:
                xs, ys = zip(*group)
                min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
                bounding_box = (min_x - group_radius, min_y - group_radius,
                                max_x + group_radius, max_y + group_radius)
                draw.ellipse(bounding_box, outline=circle_color, width=circle_width)

        full_image_path = 'all_groups.png'
        image_with_circles.save(os.path.join(settings.MEDIA_ROOT, full_image_path))

        full_images_paths.append(full_image_path)
        all_groups_paths.extend(images_paths)
    
    # Create a zip file containing all full images
    full_images_zip_filename = "all_full_images.zip"
    full_images_zip_path = os.path.join(settings.MEDIA_ROOT, full_images_zip_filename)
    with ZipFile(full_images_zip_path, 'w') as zip_file:
        for image_path in full_images_paths:
            zip_file.write(os.path.join(settings.MEDIA_ROOT, image_path),
                           os.path.basename(image_path))

    # Create a zip file containing all group images
    groups_zip_filename = "all_group_images.zip"
    groups_zip_path = os.path.join(settings.MEDIA_ROOT, groups_zip_filename)
    with ZipFile(groups_zip_path, 'w') as zip_file:
        for image_path in all_groups_paths:
            zip_file.write(os.path.join(settings.MEDIA_ROOT, image_path),
                           os.path.basename(image_path))
            
    print(len(image_paths), "images processed")

    return full_images_zip_filename, groups_zip_filename, full_image_path, all_groups_paths
