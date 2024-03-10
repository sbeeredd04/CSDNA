from PIL import Image, ImageDraw
import numpy as np
import os
from django.conf import settings

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i):
        if i != self.parent[i]:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i == root_j:
            return
        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1

def process_image(image_path, group_radius=50, min_dots=100, threshold=60, circle_color='green', circle_width=8):
    # Load the image
    original_image = Image.open(image_path)
    image_with_circles = original_image.copy()
    draw = ImageDraw.Draw(image_with_circles)
    image_array = np.array(original_image)

    # Find all dots: assuming that the dots are the only non-black pixels
    dots = np.where(np.all(image_array > threshold, axis=-1))
    dot_coordinates = list(zip(dots[1], dots[0]))

    # Helper function to check if two dots are within a certain radius
    def are_dots_close(dot1, dot2, radius=group_radius):
        return (dot1[0] - dot2[0])**2 + (dot1[1] - dot2[1])**2 <= radius**2

    # Initialize UnionFind
    uf = UnionFind(len(dot_coordinates))

    # Merge close dots into the same group
    for i, dot1 in enumerate(dot_coordinates):
        for j, dot2 in enumerate(dot_coordinates):
            if i != j and are_dots_close(dot1, dot2):
                uf.union(i, j)

    # Find groups of close dots
    grouped_dots = {}
    for i, dot in enumerate(dot_coordinates):
        root = uf.find(i)
        if root not in grouped_dots:
            grouped_dots[root] = []
        grouped_dots[root].append(dot)

    images_paths = []
    # Draw circles around groups and save individual groups
    for idx, group in enumerate(grouped_dots.values()):
        if len(group) >= min_dots:
            xs, ys = zip(*group)
            min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
            bounding_box = (min_x, min_y, max_x, max_y)
            draw.ellipse([min_x - group_radius, min_y - group_radius,
                          max_x + group_radius, max_y + group_radius],
                         outline=circle_color, width=circle_width)
            
            # Save the cropped group image without the circle
            cropped_image = original_image.crop(bounding_box)
            group_image_path = f"group_{idx}.png"
            cropped_image.save(os.path.join(settings.MEDIA_ROOT, group_image_path))
            images_paths.append(group_image_path)

    # Save the full image with circles
    full_image_path = 'all_groups.png'
    image_with_circles.save(os.path.join(settings.MEDIA_ROOT, full_image_path))

    return full_image_path, images_paths