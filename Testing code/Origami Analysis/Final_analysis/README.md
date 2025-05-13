## Origami Analysis Tool - Comprehensive User Manual

Welcome! This guide will walk you through every aspect of the Origami Analysis Tool, explaining each function, import, and line of code in plain language. No programming experience is needed—each piece is described step by step.

---

### Table of Contents

1. [Introduction](#introduction)
2. [Software Requirements](#software-requirements)
3. [Imports Explained](#imports-explained)
4. [Data Collection Functions](#data-collection-functions)

   * `collect_data`
   * `collect_group_data`
5. [Noise Filtering and Clustering](#noise-filtering-and-clustering)

   * `dbscan_filter`
   * `find_clusters_k_means`
   * `find_com`
6. [Geometric Analysis](#geometric-analysis)

   * `minimum_bounding_rectangle`
   * `distance_to_line`
   * `find_closest_side`
7. [Rotation and Orientation](#rotation-and-orientation)

   * `find_rotation_angle`
   * `rotate_points`
   * `adjust_final_orientation`
8. [Key Point Identification](#key-point-identification)

   * `find_middle_left_most_com`
   * `find_right_most_coms`
   * `find_center_of_rectangle`
   * `find_robot`
9. [Visualization Helpers](#visualization-helpers)

   * `draw_line_between_points`
   * `intersection_between_point_line`
   * `draw_line_between_point_and_line`
   * `plot_helper`
10. [Ratio Calculation and Plots](#ratio-calculation-and-plots)

    * `calculate_exact_ratio`
    * `generate_ratio_histogram`
    * `plot_ratio_points_and_lines`
11. [Categorization and Statistics](#categorization-and-statistics)

    * `input_categories`
    * `categorize_dynamically`
    * `generate_categorized_plots`
    * `gaussian_curve_generator`
    * `combine_gaussian_curves`
    * `generate_individual_gaussian_curve`
12. [Main Processing Functions](#main-processing-functions)

    * `process_origami_ratio`
    * `process_multiple_origami_ratio_with_categorize_and_gaussian`
13. [Using the Tool - Step by Step](#using-the-tool---step-by-step)
14. [Troubleshooting](#troubleshooting)
15. [Glossary](#glossary)

---

## Introduction

This Python-based tool analyzes DNA origami microscopy data, identifies key structural features, aligns them, measures characteristic ratios, and visualizes results. We will break down each piece of code so you know exactly what happens under the hood.

## Software Requirements

Make sure you have:

* **Python 3.6+**: The programming language that runs the tool.
* **Packages** (install via `pip install numpy pandas matplotlib seaborn scipy scikit-learn h5py`):

  * `numpy`: for numerical operations on arrays
  * `pandas`: for table-like data management
  * `matplotlib` & `seaborn`: for charts and plots
  * `scipy`: for geometry and statistics functions
  * `scikit-learn`: for clustering algorithms
  * `h5py`: for reading HDF5 data files

## Imports Explained

At the top of the code, we bring in necessary modules:

```python
import numpy as np           # shorthand np for numerical array work
import pandas as pd          # shorthand pd for table-like data
from sklearn.cluster import KMeans, DBSCAN  # clustering methods
import h5py                  # read .h5 data files
from scipy.spatial import ConvexHull          # find convex hull of points
ing** repeated imports removed for clarity **
import matplotlib.pyplot as plt  # plotting library
import seaborn as sns            # statistical plotting
from scipy.spatial.distance import cdist # compute distances
tfrom sklearn.metrics import silhouette_score # cluster quality metric
from scipy.stats import norm       # normal distribution functions
import pickle                     # save/load Python objects\import os                         # file path operations
```

* **Why import twice?** Some functions (like `ConvexHull`) appear more than once; it doesn’t cause problems but can be cleaned up.

---

## Data Collection Functions

### `collect_data(filename)`

Reads an HDF5 file, extracts `x` and `y` coordinates, and returns a table (`DataFrame`).

```python
def collect_data(filename):
    # 1. Open file in read-only mode
    with h5py.File(filename, 'r') as f:
        locs = f['locs']         # access group "locs"
        x_values = locs['x'][:]   # read all x coordinates
        y_values = locs['y'][:]   # read all y coordinates
    data = {'x': x_values, 'y': y_values}
    return pd.DataFrame(data)     # return as table with columns x, y
```

* **Line by line**:

  1. **`with h5py.File`**: safely open file, auto-closes.
  2. **`f['locs']`**: get the dataset named `locs`.
  3. **`[:]`**: slice notation reads entire dataset.
  4. **`pd.DataFrame`**: creates an easy-to-use table.

### `collect_group_data(hdf5_file, dataset_name)`

Extracts multiple groups (e.g., several experiments) from one file.

```python
def collect_group_data(hdf5_file, dataset_name):
    group_data_list = []
    with h5py.File(hdf5_file, 'r') as f:
        dataset = f[dataset_name]
        group_data = dataset['group'][:]  # group IDs array
        x_data = dataset['x'][:]         # x coords array
        y_data = dataset['y'][:]         # y coords array
        unique_groups = np.unique(group_data) # find IDs present
        for group in unique_groups:
            indices = np.where(group_data == group)
            group_dict = {'group': int(group),
                          'x': x_data[indices].tolist(),
                          'y': y_data[indices].tolist()}
            group_data_list.append(group_dict)
    return group_data_list
```

* **Key points**:

  * **`np.unique`** finds each distinct group label.
  * For each group:

    * **`np.where`** locates positions matching that label.
    * We store the lists of `x` and `y` for that group.

---

## Noise Filtering and Clustering

### `dbscan_filter(data, eps, min_samples)`

Removes noise/outliers using DBSCAN.

```python
def dbscan_filter(data, eps=0.05, min_samples=5):
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
    core_samples = clustering.core_sample_indices_
    return data.iloc[core_samples]
```

* **`eps`**: distance threshold to consider neighbors.
* **`min_samples`**: minimum neighbors to keep a point.
* We return only `core` points, dropping loose outliers.

### `find_clusters_k_means(data, k)`

Groups points into `k` clusters.

```python
def find_clusters_k_means(data, k):
    kmeans = KMeans(init="k-means++", n_clusters=k, tol=1e-8,
                     n_init=8, max_iter=1000)
    kmeans.fit(data)
    return kmeans.labels_
```

* **`init="k-means++"`**: smart starting position.
* **`n_init`**: how many times to retry.
* Returns an array of cluster numbers for each point.

### `find_com(data, labels)`

Computes the average position (center) of each cluster.

```python
def find_com(data, labels):
    com = []
    for i in range(max(labels)+1):
        x = np.mean(data['x'][labels == i])
        y = np.mean(data['y'][labels == i])
        com.append((x, y))
    return com
```

* **Loop** from first cluster (0) to last (`max(labels)`).
* **`np.mean`** finds center along `x` and `y`.

---

## Geometric Analysis

### `minimum_bounding_rectangle(points)`

Finds the smallest rotated rectangle covering all `points`.

Key steps:

1. Compute convex hull (`ConvexHull`), lighter boundary.
2. For each edge angle, rotate points, find bounding box area.
3. Choose smallest area; compute its corners.

A detailed breakdown is in-code comments.

### `distance_to_line(point, line_start, line_end)`

Computes perpendicular distance from `point` to the line segment.

```python
def distance_to_line(point, line_start, line_end):
    if np.all(line_start == line_end):
        return np.linalg.norm(point - line_start)
    return np.abs(np.cross(line_end - line_start,
                       point - line_start)
                  / np.linalg.norm(line_end - line_start))
```

* **Handles degenerate line** (start==end).
* Uses vector cross product formula.

### `find_closest_side(points, rectangle)`

Finds which rectangle side has the 4 nearest COMs with the smallest maximum distance.

1. For each side (4 total): measure all COM distances.
2. Sort, keep 4 smallest.
3. Compare the 4-distance sets; choose side where the largest of those 4 is minimal.

---

## Rotation and Orientation

### `find_rotation_angle(rectangle, closest_side)`

Calculates angle needed so that `closest_side` aligns to the top.

* Computes raw angle via `atan2`.
* Adjusts by 90° or 180° depending on orientation.
* Returns negative angle for correct plotting rotation.

### `rotate_points(points, rotation_angle, pivot)`

Rotates an array of points around `pivot` by `rotation_angle`.

```python
def rotate_points(points, rotation_angle, pivot):
    rotation_matrix = [[cos, -sin], [sin, cos]]
    return (points - pivot) @ rotation_matrix.T + pivot
```

### `adjust_final_orientation(...)`

Fine-tunes orientation by comparing the rectangle before/after a 180° flip.

---

## Key Point Identification

### `find_middle_left_most_com(rotated_com)`

Among three leftmost COMs (smallest x), finds the one that is neither topmost nor bottommost by y.

### `find_right_most_coms(rotated_com)`

Selects the two points with highest x values.

### `find_center_of_rectangle(rectangle)`

Simple average of corner coordinates for rectangle center.

### `find_robot(rotated_com)`

Custom logic:

1. Remove left 3, right 2, top 4 COMs.
2. From remaining, pick one nearest the convex hull center.
3. If none remain, use hull center.

---

## Visualization Helpers

### `draw_line_between_points(p1, p2)`

Plots a line connecting two points.

### `intersection_between_point_line(point, line)`

Finds intersection point if a perpendicular line dropped from `point` meets `line`.

### `draw_line_between_point_and_line(p1, p2, p3)`

Draws the perpendicular line from `p3` to the line defined by `(p1,p2)`.

### `plot_helper(...)`

Unified plotting function that can display raw data, clusters, COMs, rectangles, and special points in one figure. Uses black background, inverts y-axis, and labels each element for clarity.

---

## Ratio Calculation and Plots

### `calculate_exact_ratio(...)`

1. Defines right-hand line via two rightmost COMs.
2. Measures perpendicular distance from robot COM and from second-highest COM.
3. Ratio = robot distance / normalizing distance.
4. Plots data, COMs, reference lines, clusters, and ratio components in a single annotated chart.
5. Returns the numeric ratio.

### `generate_ratio_histogram(ratios, bins, title, ...)`

Produces a histogram of ratio values.

### `plot_ratio_points_and_lines(ratios, ...)`

Plots ratio values as connected points, annotating each.

---

## Categorization and Statistics

### `input_categories()`

Prompts you to define category names in the console.

### `categorize_dynamically(group_num, ratio, categories)`

After each group is processed, asks which category to assign it to.

### `generate_categorized_plots(categories)`

For each category, plots histograms and line charts of ratios.

### `gaussian_curve_generator(categories)`

Computes mean & standard deviation of ratios per category and plots normal distribution curves.

### `combine_gaussian_curves(curve1, curve2, ...)`

Overlays two Gaussian curves for comparison.

### `generate_individual_gaussian_curve(category, gaussian_curves)`

Plots the normal curve for just one category.

---

## Main Processing Functions

### `process_origami_ratio(filename, k)`

Runs the step-by-step pipeline on a single file:

1. Load data
2. K-means clustering
3. Compute COMs
4. Minimum bounding rectangle
5. Find orientation
6. Rotate points & COMs
7. Adjust orientation
8. Identify key COMs
9. Calculate ratio & show chart

It calls all previous helper functions in sequence.

### `process_multiple_origami_ratio_with_categorize_and_gaussian(...)`

Extended pipeline:

* Loads or defines categories
* Iterates over multiple groups in one file
* Filters noise, clusters, computes COMs, rotates, identifies points
* Calculates ratio per group, prompts categorization
* Saves category assignments
* Generates summary plots and Gaussian analysis

---

## Using the Tool - Step by Step

1. **Prepare data file**: Have HDF5 file(s) with `locs` group containing `x`,`y` arrays.
2. **Basic run** for a single structure:

   ```python
   ratio = process_origami_ratio('your_file.h5', k=10)
   ```
3. **Multiple & categorize**:

   ```python
   ratios, categories, curves = process_multiple_origami_ratio_with_categorize_and_gaussian(
       'your_file.h5', k=10, flipped=False)
   ```
4. **Follow prompts**: Define categories, assign each group.
5. **Review outputs**: Charts pop up; summary objects returned in Python.

---

## Troubleshooting

* **Missing points**: Tweak `eps` or `min_samples` in `dbscan_filter`.
* **Wrong cluster count**: Increase/decrease `k`.
* **Flipped images**: Pass `flipped=True` to the pipeline.
* **Pickle issues**: Delete `categories.pkl` to reset categories.

---

## Glossary

* **COM**: Center of Mass, average position of a cluster.
* **DBSCAN**: Density-Based clustering algorithm.
* **K-means**: Partitioning clustering grouping points into k clusters.
* **Convex Hull**: The smallest convex boundary that encloses all points.
* **Pivot**: A reference point for rotation.
* **Pickle**: Python object serialization format.

---

*End of Manual.*
