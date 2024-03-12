from PIL import Image, ImageDraw
import numpy as np
import os
from django.conf import settings
from zipfile import ZipFile
import glob

# Attempt to import cuml's DBSCAN for GPU acceleration; fall back to sklearn if unavailable
try:
    from cuml.cluster import DBSCAN
    use_gpu = True
    print("Using GPU for DBSCAN")
except ImportError:
    from sklearn.cluster import DBSCAN
    use_gpu = False

def process_images(input_path, group_radius=50, min_dots=100, threshold=60, circle_color='green', circle_width=8):
    if os.path.isdir(input_path):
        image_paths = glob.glob(os.path.join(input_path, '*.png'))
    else:
        image_paths = [input_path]
    
    full_images_paths = []
    all_groups_paths = []

    for image_path in image_paths:
        original_image = Image.open(image_path)
        image_array = np.array(original_image)

        dots = np.where(np.all(image_array > threshold, axis=-1))
        dot_coordinates = np.array(list(zip(dots[1], dots[0])))

        # Pass appropriate parameters based on the backend (cuml or sklearn)
        if use_gpu:
            db = DBSCAN(eps=group_radius, min_samples=6, metric='euclidean', output_type='numpy').fit(dot_coordinates)
        else:
            db = DBSCAN(eps=group_radius, min_samples=6).fit(dot_coordinates)

        labels = db.labels_
        unique_labels = set(labels)

        grouped_dots = {label: [] for label in unique_labels if label != -1}

        for label, dot in zip(labels, dot_coordinates):
            if label != -1:
                grouped_dots[label].append(dot)

        images_paths = []
        for idx, group in enumerate(grouped_dots.values()):
            if len(group) >= min_dots:
                xs, ys = zip(*group)
                min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
                bounding_box = [max(min_x - group_radius, 0), max(min_y - group_radius, 0),
                                min(max_x + group_radius, original_image.width), min(max_y + group_radius, original_image.height)]
                cropped_image = original_image.crop(bounding_box)
                group_image_path = f"group_{idx}.png"
                cropped_image.save(os.path.join(settings.MEDIA_ROOT, group_image_path))
                images_paths.append(group_image_path)

        image_with_circles = original_image.copy()
        draw = ImageDraw.Draw(image_with_circles)
        for group in grouped_dots.values():
            if len(group) >= min_dots:
                xs, ys = zip(*group)
                min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
                draw.ellipse((min_x - group_radius, min_y - group_radius, max_x + group_radius, max_y + group_radius),
                             outline=circle_color, width=circle_width)

        full_image_path = 'all_groups.png'
        image_with_circles.save(os.path.join(settings.MEDIA_ROOT, full_image_path))
        full_images_paths.append(full_image_path)
        all_groups_paths.extend(images_paths)

    full_images_zip_filename = "all_full_images.zip"
    full_images_zip_path = os.path.join(settings.MEDIA_ROOT, full_images_zip_filename)
    with ZipFile(full_images_zip_path, 'w') as zip_file:
        for path in full_images_paths:
            zip_file.write(os.path.join(settings.MEDIA_ROOT, path), os.path.basename(path))

    groups_zip_filename = "all_group_images.zip"
    groups_zip_path = os.path.join(settings.MEDIA_ROOT, groups_zip_filename)
    with ZipFile(groups_zip_path, 'w') as zip_file:
        for path in all_groups_paths:
            zip_file.write(os.path.join(settings.MEDIA_ROOT, path), os.path.basename(path))
    
    print(f"{len(image_paths)} images processed using {'GPU' if use_gpu else 'CPU'}")

    return full_images_zip_filename, groups_zip_filename, full_image_path, all_groups_paths
