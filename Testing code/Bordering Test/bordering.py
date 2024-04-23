import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import math

# Load the image
image_path = 'Testing code\Bordering Test\Clean_csDNA\group_37.png'  # Replace with your image path
image = cv2.imread(image_path)

# Convert to grayscale
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply threshold to get rid of background
_, thresholded_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# List to hold centers of spots
centers = []

# Loop through each contour
for contour in contours:
    # Calculate image moments of the contour
    M = cv2.moments(contour)
    
    # Using the moments, calculate the centroid (center of the spot)
    if M["m00"] != 0:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        centers.append([cX, cY])

# Assuming 'centers' is your list of center points
centers_array = np.array(centers)

# Compute the convex hull
hull = ConvexHull(centers_array)

# Define a function to check if a point is close to a line segment
def is_point_close_to_line(pt, line_start, line_end, threshold):
    line_magnitude = np.linalg.norm(line_end - line_start)
    distance = np.abs(np.cross(line_end-line_start, line_start-pt)) / line_magnitude
    return distance < threshold

# Compute the length of each edge and check the distance of other points from the edge
valid_edges = []
for edge in hull.simplices:
    line_start, line_end = centers_array[edge[0]], centers_array[edge[1]]
    edge_length = np.linalg.norm(line_end - line_start)
    is_valid = True
    for point_index in range(len(centers_array)):
        if point_index not in edge:
            if is_point_close_to_line(centers_array[point_index], line_start, line_end, 5):
                is_valid = False
                break
    if is_valid:
        valid_edges.append((edge_length, edge))

# Now find the longest valid edge
if valid_edges:
    longest_edge = max(valid_edges, key=lambda x: x[0])[1]

# Assuming you have found the 'longest_edge' using the previous steps
point1, point2 = centers_array[longest_edge[0]], centers_array[longest_edge[1]]

# Create a plot
plt.figure(figsize=(6, 6))

# Plot all the centers as blue dots
plt.scatter(centers_array[:, 0], centers_array[:, 1], color='blue', s=20)

# Plot all the edges of the hull as black lines
for simplex in hull.simplices:
    plt.plot(centers_array[simplex, 0], centers_array[simplex, 1], 'k-')

# Highlight the longest edge in green
plt.plot(centers_array[longest_edge, 0], centers_array[longest_edge, 1], color='green', linewidth=2)

# Invert the y-axis to match image coordinates
plt.gca().invert_yaxis()

# Show the plot
plt.axis('off')  # Hide the axes
plt.show()

print(str(point1))
print(str(point2))

dx = point2[0] - point1[0]
dy = (-1)*point2[1] - (-1)*point1[1]

angle_of_rotation = np.arctan2(dy, dx)

# Compute the angle to horizontal
angle_to_horizontal = np.degrees(angle_of_rotation)
print("degrees:" + str(angle_to_horizontal))
# If the angle is negative, we rotate counter-clockwise by its absolute value
rotation_angle = 180-angle_to_horizontal if angle_to_horizontal < 0 else 360-angle_to_horizontal

# Compute center for rotation, which is the midpoint of the longest line
rotation_center = ((point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2)

# Compute rotation matrix
rotation_matrix = cv2.getRotationMatrix2D(rotation_center, rotation_angle, 1.0)

# Perform the rotation
(h, w) = gray_image.shape[:2]
rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

# Apply this rotation to each center point
rotated_centers = np.vstack([np.dot(rotation_matrix, np.array([*center, 1])) for center in centers_array])

# Recalculate the hull for visual consistency in plot, though it's not necessary for rotation proof
rotated_hull = ConvexHull(rotated_centers)

# Plot the rotated image
plt.figure(figsize=(6, 6))
plt.imshow(cv2.cvtColor(rotated_image, cv2.COLOR_BGR2RGB))

# Plot the rotated center points as blue dots
plt.scatter(rotated_centers[:, 0], rotated_centers[:, 1], color='blue', s=20)

# Highlight the longest valid rotated edge in green
plt.plot(rotated_centers[longest_edge, 0], rotated_centers[longest_edge, 1], color='green', linewidth=2)

plt.axis('off')  # Hide the axes
plt.show()