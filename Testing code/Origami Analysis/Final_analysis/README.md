## Origami Analysis Tool - Comprehensive User Manual

Welcome! This guide will walk you through every aspect of the Origami Analysis Tool, explaining each function, import, and line of code in plain language. No programming experience is needed—each piece is described step by step.
*Think of this like a recipe book that tells you exactly what ingredients and steps you need.*

---

### Table of Contents

1. [Introduction](#introduction)
   *What this whole tool is for.*
2. [Software Requirements](#software-requirements)
   *What you need before you start.*
3. [Imports Explained](#imports-explained)
   *Like gathering your kitchen tools.*
4. [Data Collection Functions](#data-collection-functions)
   *How we read the picture data.*

   * `collect_data`
   * `collect_group_data`
5. [Noise Filtering and Clustering](#noise-filtering-and-clustering)
   *How we clean up and group the dots.*

   * `dbscan_filter`
   * `find_clusters_k_means`
   * `find_com`
6. [Geometric Analysis](#geometric-analysis)
   *How we draw boxes and lines around dots.*

   * `minimum_bounding_rectangle`
   * `distance_to_line`
   * `find_closest_side`
7. [Rotation and Orientation](#rotation-and-orientation)
   *How we turn the shape the right way up.*

   * `find_rotation_angle`
   * `rotate_points`
   * `adjust_final_orientation`
8. [Key Point Identification](#key-point-identification)
   *How we pick the special dots.*

   * `find_middle_left_most_com`
   * `find_right_most_coms`
   * `find_center_of_rectangle`
   * `find_robot`
9. [Visualization Helpers](#visualization-helpers)
   *How we draw pictures on the screen.*

   * `draw_line_between_points`
   * `intersection_between_point_line`
   * `draw_line_between_point_and_line`
   * `plot_helper`
10. [Ratio Calculation and Plots](#ratio-calculation-and-plots)
    *How we measure and show results.*

    * `calculate_exact_ratio`
    * `generate_ratio_histogram`
    * `plot_ratio_points_and_lines`
11. [Categorization and Statistics](#categorization-and-statistics)
    *How we sort and analyze numbers.*

    * `input_categories`
    * `categorize_dynamically`
    * `generate_categorized_plots`
    * `gaussian_curve_generator`
    * `combine_gaussian_curves`
    * `generate_individual_gaussian_curve`
12. [Main Processing Functions](#main-processing-functions)
    *The big steps that use everything else.*

    * `process_origami_ratio`
    * `process_multiple_origami_ratio_with_categorize_and_gaussian`
13. [Using the Tool - Step by Step](#using-the-tool---step-by-step)
    *How to run this tool like a recipe.*
14. [Troubleshooting](#troubleshooting)
    *Fixing common hiccups.*
15. [Glossary](#glossary)
    \*Easy definitions.

---

## Introduction

This Python-based tool analyzes DNA origami microscopy data—think of points on a picture—to find special shapes, lines, and measurements. It helps scientists measure tiny structures by:

1. Finding clusters of points (like finding groups of stars in the sky).
2. Drawing a tight box around those stars.
3. Turning the box so its closest side is easy to compare.
4. Picking out special stars (dots) to measure distances and get a final number (ratio).

*Imagine you had a connect-the-dots picture and wanted to know how far the “rocket” is from the “moon.” This tool does that automatically!*

---

## Software Requirements

Make sure you have everything installed, like gathering ingredients before cooking:

* **Python 3.6+**: The language our tool is written in, like English for recipes.
* **Packages** (install with `pip install numpy pandas matplotlib seaborn scipy scikit-learn h5py`):

  * `numpy`: handles lists of numbers fast (like a calculator).
  * `pandas`: organizes numbers into tables (like spreadsheets).
  * `matplotlib` & `seaborn`: make charts and pictures (like drawing on paper).
  * `scipy`: does geometry and math helpers (like a ruler and protractor).
  * `scikit-learn`: finds groups and patterns (like sorting colored beads).
  * `h5py`: reads our special data file (.h5) (like opening a locked box).

---

## Imports Explained

At the top of the code we gather our tools:

```python
import numpy as np           # calculator for arrays of numbers
import pandas as pd          # table manager, like Excel
from sklearn.cluster import KMeans, DBSCAN  # for grouping points
import h5py                  # to open our HDF5 files
from scipy.spatial import ConvexHull          # finds the outer shell of points
import matplotlib.pyplot as plt  # to draw plots
import seaborn as sns            # nicer plot styles
from scipy.spatial.distance import cdist # easy distance calculations
from scipy.stats import norm       # for bell-curve math
import pickle                     # save/load Python objects, like bookmarks
import os                         # work with file paths
```

*We won’t change these lines; we just need them to use each tool.*

---

## Data Collection Functions

Here we explain how we read the raw coordinates from files.

### `collect_data(filename)`

**Purpose**: Open a file and pull out two lists: all X positions and all Y positions of points.
**Why?** We need the raw dot coordinates before we can sort or measure anything.

```python
def collect_data(filename):
    # 1. Open file in read-only mode safely
    with h5py.File(filename, 'r') as f:
        locs = f['locs']         # find the 'locs' section
        x_values = locs['x'][:]   # grab all x values
        y_values = locs['y'][:]   # grab all y values
    data = {'x': x_values, 'y': y_values}
    return pd.DataFrame(data)     # return a table with columns 'x' and 'y'
```

*Imagine you have a map with marked spots; this gives you two lists of numbers: left-right (x) and up-down (y).*

### `collect_group_data(hdf5_file, dataset_name)`

**Purpose**: Do the same, but when your file has multiple groups of points (like multiple pictures inside one book).
**Why?** So we can process each group separately.

```python
def collect_group_data(hdf5_file, dataset_name):
    group_data_list = []
    with h5py.File(hdf5_file, 'r') as f:
        dataset = f[dataset_name]
        group_data = dataset['group'][:]  # which dot belongs to which picture
        x_data = dataset['x'][:]         # all x positions
        y_data = dataset['y'][:]         # all y positions
        unique_groups = np.unique(group_data) # list of pictures present
        for group in unique_groups:
            indices = np.where(group_data == group)
            group_dict = {'group': int(group),
                          'x': x_data[indices].tolist(),
                          'y': y_data[indices].tolist()}
            group_data_list.append(group_dict)
    return group_data_list
```

*Think of a photo album: this splits the dots by each photo so you can look at one at a time.*

---

## Noise Filtering and Clustering

Now we clean up stray dots and group the rest into clusters (like sorting marbles by color).

### `dbscan_filter(data, eps, min_samples)`

**Purpose**: Remove stray dots that are too far from others.
**Why?** To focus on real points, not random specks.

```python
def dbscan_filter(data, eps=0.05, min_samples=5):
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
    core_samples = clustering.core_sample_indices_
    return data.iloc[core_samples]
```

* **`eps`**: how close dots must be to count as a group.
* **`min_samples`**: how many neighbors needed.

*Like brushing away dust, leaving only clusters of marbles on the floor.*

### `find_clusters_k_means(data, k)`

**Purpose**: Divide the cleaned dots into exactly `k` groups.
**Why?** So we know distinct clusters to analyze separately.

```python
def find_clusters_k_means(data, k):
    kmeans = KMeans(init="k-means++", n_clusters=k, tol=1e-8,
                     n_init=8, max_iter=1000)
    kmeans.fit(data)
    return kmeans.labels_
```

*Imagine sorting 20 candies into 4 bowls by shape—this picks which candy goes in which bowl.*

### `find_com(data, labels)`

**Purpose**: Find the center point of each group (cluster).
**Why?** These centers help us draw a nice tight box and pick key points.

```python
def find_com(data, labels):
    com = []
    for i in range(max(labels)+1):
        x = np.mean(data['x'][labels == i])
        y = np.mean(data['y'][labels == i])
        com.append((x, y))
    return com
```

*Like finding the center of each bowl of candies.*

---

## Geometric Analysis

We draw a smallest possible rectangle—like wrapping a present around the candy centers.

### `minimum_bounding_rectangle(points)`

**Purpose**: Find the smallest tilted box that covers all your cluster centers.
**Why?** It gives a standardized frame of reference for measuring.

*Imagine turning a piece of paper until it just fits around all the stars on a page.*

### `distance_to_line(point, line_start, line_end)`

**Purpose**: Measure how far a dot is from a line.
**Why?** To find the best side of the box.

*Like dropping a perpendicular from a dot to the edge of a shape.*

### `find_closest_side(points, rectangle)`

**Purpose**: Pick which side of that box has the four nearest centers.
**Why?** That side will be our “base” to line everything up.

*Think of choosing the flattest edge of a block to set it on a table.*

---

## Rotation and Orientation

We rotate the box so that its chosen side is level at the bottom (or top).

### `find_rotation_angle(rectangle, closest_side)`

**Purpose**: Calculate how many degrees to turn the box so the closest side is horizontal.
**Why?** So every measurement is consistent.

### `rotate_points(points, rotation_angle, pivot)`

**Purpose**: Turn all your dots and centers around a fixed point by that angle.
**Why?** So dots, centers, and box all rotate together.

### `adjust_final_orientation(...)`

**Purpose**: Optionally flip 180° if it makes the shape’s key side face up rather than down.
**Why?** To standardize orientation (so every picture looks the same side up).

---

## Key Point Identification

Once everything is level, we pick exactly which centers to measure:

### `find_middle_left_most_com(rotated_com)`

* Finds 3 leftmost points, then picks the one in the middle vertically.

### `find_right_most_coms(rotated_com)`

* Finds the two rightmost points.

### `find_center_of_rectangle(rectangle)`

* Finds the rectangle’s center.

### `find_robot(rotated_com)`

* A special method that removes some points by rules (left 3, right 2, top 4) then picks the closest to the hull’s center.
  *This final point is like the “robot” or main feature we compare to others.*

---

## Visualization Helpers

We draw helpful pictures at each step:

* `draw_line_between_points`: Draws a straight line between two points.
* `intersection_between_point_line`: Finds where a dot meets a line at a right angle.
* `draw_line_between_point_and_line`: Draws that perpendicular line.
* `plot_helper`: A one-stop function to show dots, clusters, boxes, and special points on a dark background.

*These plots help you visually confirm each step, like looking at ingredients as you add them.*

---

## Ratio Calculation and Plots

Now we measure and show our final number.

### `calculate_exact_ratio(...)`

1. Draw a line between the two rightmost points.
2. Measure distance from the special “robot” point to that line.
3. Measure distance from the “second-highest” point to the same line.
4. Ratio = (robot distance) / (second-highest distance).
5. Show a colorful plot with clusters, points, lines, and labels.

*This ratio helps scientists compare structures easily.*

### `generate_ratio_histogram(ratios, ...)`

* Shows how many structures fall into each ratio range.

### `plot_ratio_points_and_lines(ratios, ...)`

* Plots each ratio as a dot on a line, so you can spot peaks and valleys.

---

## Categorization and Statistics

We sort structures into named groups and analyze numbers.

### `input_categories()`

* Ask you to type in category names (like “Good”, “Bad”, “Ugly”).

### `categorize_dynamically(group_num, ratio, categories)`

* After each analysis, you pick which bucket the ratio goes into.

### `generate_categorized_plots(categories)`

* For each bucket, draw histograms and line plots of ratios in it.

### `gaussian_curve_generator(categories)`

* For each bucket, find its average (mean) and spread (standard deviation) then draw a smooth bell curve.

### `combine_gaussian_curves(curve1, curve2, ...)`

* Lay two bell curves on top of each other for comparison.

### `generate_individual_gaussian_curve(category, gaussian_curves)`

* Draw the bell curve for one category only.

*These stats help you understand patterns across many structures.*

---

## Main Processing Functions

These are the “recipes” that use all helpers above in order.

### `process_origami_ratio(filename, k)`

1. Read data.
2. Group dots & find centers.
3. Draw minimal box & pick a side.
4. Rotate everything level.
5. Identify key points.
6. Measure ratio & show plot.
7. Return the numeric result.

### `process_multiple_origami_ratio_with_categorize_and_gaussian(...)`

1. Load or define category names.
2. For each group in file: clean, cluster, rotate, identify, measure.
3. Ask you which category the result fits.
4. Save your buckets to a file.
5. At end, show summary plots and bell curves.

*Use these to analyze one or many structures with ease.*

---

## Using the Tool - Step by Step

1. **Prepare data**: Have your HDF5 file(s) ready with points stored under `locs`.
2. **Single run**: Type:

   ```python
   ratio = process_origami_ratio('your_file.h5', k=10)
   ```
3. **Multiple + categorize**: Type:

   ```python
   ratios, categories, curves = process_multiple_origami_ratio_with_categorize_and_gaussian(
       'your_file.h5', k=10, flipped=False)
   ```
4. **Name your buckets** when prompted (e.g., "Type A", "Type B").
5. **Assign each structure** by typing a bucket name.
6. **View results**: Histograms, line plots, and bell curves will pop up.

*It’s like following a cooking recipe—read ingredients, follow steps, enjoy the meal!*

---

## Troubleshooting

* **Missing points**: Increase how many neighbors need to group (`min_samples`) or let them be a bit farther (`eps`).
* **Wrong cluster count**: Change `k` up or down.
* **Flipped pictures**: Add `flipped=True` to match orientation.
* **Pickle file issues**: Delete `categories.pkl` and start fresh.

---

## Glossary

* **COM**: Center of Mass—the average dot of a cluster.
* **DBSCAN**: A way to ignore stray dots and keep real groups.
* **K-means**: A way to split dots into exactly k groups.
* **Convex Hull**: The outer shell that wraps around all points.
* **Pivot**: A fixed point around which we rotate.
* **Pickle**: A way to save your category choices for next time.

---

*End of Manual.*
