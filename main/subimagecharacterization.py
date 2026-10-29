# This script takes subimages from the OOF workflow and completes
# microstructure characterization to help inform SM and SA workflows

from pathlib import Path
import logging
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

## ========================================== ##
# Define Threshold and Key Values #
# Phase Threshold Values
void_threshold = 0
matrix_threshold = 120
fiber_threshold = 255
# Measurement Values
# Line 70 - confirm minimum distance between objects is realistic
minimum_object_size = 1
minimum_object_distance = 1
pixel_size_um = 1 # conversion for length of pixel in um
## ========================================== ##

## ========================================== ##
# 1. Ensure Image is Greyscale #
def read_mask(image_path):
    image_path = Path(image_path)
    with Image.open(image_path) as image:
        image = np.asarray(image)
    if image.ndim == 3:
        if image.shape[2] == 4:
            image = image[:, :, :3]

        if image.shape[2] != 3:
            raise ValueError((f"Unsupported image format"))
        if not (np.array_equal(image[:, :, 0], image[:, :, 1]) and np.array_equal(image[:, :, 1], image[:, :, 2])):
            raise ValueError(f"Image is not greyscale")
        image = image[:, :, 0]
    if image.ndim != 2:
        raise ValueError(f"Expected a 2D greyscale image")

    if not np.issubdtype(image.dtype, np.integer):
        raise ValueError(f"Threshold values are not integers")
    return image.astype(np.uint8, copy = False)
## ========================================== ##

## ========================================== ##
# 2. Define Phases in Subimage #
def define_phase(image):
    mask = np.asarray(image)
    return{"void": mask == void_threshold, "matrix": mask == matrix_threshold, "fiber": mask == fiber_threshold}
## ========================================== ##

## ========================================== ##
# 3. Label Fibers and Voids
def define_inclusions(binary_mask, split_touching = True):
    # THis section uses a distance-transform watershed to split
    # touching fibers. Use visual validation in final images
    if not np.any(binary_mask):
        return np.zeros(binary_mask.shape, dtype = np.int32)
    if not split_touching:
        return label(binary_mask, connectivity = 2)

    distance = distance_transform_edt(binary_mask)
    coordinates = peak_local_max(distance, labels = binary_mask.astype(np.uint8), min_distance = 3, exclude_border = False)
    if len(coordinates) == 0:
        return label(binary_mask, connectivity = 2)
    markers = np.zeros(binary_mask.shape, dtype = np.int32)
    for marker_id, (row, col) in enumerate(coordinates, start = 1):
        markers[row, col] = marker_id
    return watershed(-distance, markers, mask = binary_mask)
## ========================================== ##

## ========================================== ##
# 4. Measure Individual Fibers and Voids
# This function will measure the morphology of the detected objects
# Measurements: area, eq. diameter, axes, AR, eccentricity, solidity, circularity, orientation, centroid X/Y, border contact
def measure_objects(binary_mask, phase_name, pixel_size_um, min_area_px = 3, split_touching = True):
    cleaned_mask = remove_small_objects(binary_mask.astype(bool), min_size = max(1, int(min_area_px)), connectivity = 2)
    labeled_mask = define_inclusions(cleaned_mask, split_touching = (split_touching and phase_name == "fiber"),)
    properties = regionprops(labeled_mask)
    rows = []
    image_height, image_width = binary_mask.shape
    for object_id, prop in enumerate(properties, start = 1):
        area_px = float(prop.area)
        area_um2 = area_px * pixel_size_um ** 2
        equivalent_diameter_px = float(prop.equivalent_diameter_area)
        equivalent_diameter_um = equivalent_diameter_px * pixel_size_um
        major_axis_px = float(prop.major_axis_length)
        major_axis_um = major_axis_px * pixel_size_um
        minor_axis_px = float(prop.minor_axis_length)
        minor_axis_um = minor_axis_px * pixel_size_um
        perimeter_px = float(prop.perimeter)
        perimeter_um = perimeter_px * pixel_size_um
        if perimeter_px > 0:
            circularity = (4.0 * np.pi * area_px / perimeter_px ** 2)
        else:
            circularity = np.nan
        min_row, min_col, max_row, max_col = prop.bbox
        touches_border = (min_row == 0 or min_col == 0 or max_row == image_height or max_col == image_width)
        centroid_Y, centroid_X = prop.centroid
        centroid_X_um = centroid_X * pixel_size_um
        centroid_Y_um = centroid_Y * pixel_size_um

        rows.append({"phase": phase_name, "object_id": object_id, "area_pixel": area_px, "area_um2": area_um2, "equivalent_diameter_pixel": equivalent_diameter_px, "equivalent_diameter_um": equivalent_diameter_um,
                     "major_axis_um": major_axis_um, "minor_axis_um": minor_axis_um, "aspect_ratio_major_minor": (major_axis_px / minor_axis_px if minor_axis_px > 0 else np.nan), "eccentricity": float(prop.eccentricity),
                     "solidity": float(prop.solidity), "circularity": circularity, "orientation_degrees": float(np.degrees(prop.orientation)), "centroid_X_um": float(centroid_X_um), "centroid_Y_um": float(centroid_Y_um), "touches_border": bool(touches_border),})
    
    return pd.DataFrame(rows)
## ========================================== ##

## ========================================== ##
# 5. Calculation of Phase Area Fractions
def phase_summary(mask, pixel_size_um):
    height, width = mask.shape
    total_pixels = height * width
    total_area_um2 = total_pixels * pixel_size_um ** 2
    phase_rows = []
    for phase_name, phase_mask in define_phase(mask).items():
        pixel_count = int(np.count_nonzero(phase_mask))
        area_um2 = pixel_count * pixel_size_um ** 2
        fraction = (pixel_count / total_pixels if total_pixels > 0 else np.nan)
        phase_rows.append({"phase": phase_name, "pixel_count": pixel_count, "area_um2": area_um2, "area_fraction": fraction})

    return pd.DataFrame(phase_rows), total_area_um2
## ========================================== ##

## ========================================== ##
# 6. Statistics
def summarize(objects, phase_name):
    if objects.empty:
        subset = objects
    else:
        subset = objects[objects["phase"] == phase_name]
    prefix = phase_name
    result = {f"{prefix}_count": int(len(subset)), f"{prefix}_border_count": (int(subset["touches_border"].sum()) if not subset.empty else 0),}
    metrics = {"area_um2": ["mean", "std", "median", "max"], "equivalent_diameter_um": ["mean", "std", "median", "max"], "aspect_ratio_major_minor": ["mean", "std"],
              "circularity": ["mean", "std"], "eccentricity": ["mean", "std"], "solidity": ["mean", "std"]}
    for column, aggregations in metrics.items():
        for aggregation in aggregations:
            key = f"{prefix}_{column}_{aggregation}"
            if subset.empty:
                value = np.nan
            else:
                series = subset[column]
                
                if aggregation == "mean":
                    value = series.mean()
                elif aggregation == "std":
                    value = (series.std(ddof = 1) if len(series) > 1 else np.nan)
                elif aggregation == "median":
                    value = series.median()
                elif aggregation == "max":
                    value = series.max()
                else:
                    value = np.nan
            result[key] = value
    return result
## ========================================== ##

## ========================================== ##
# 7. Spatial Statistics
# Centroid to centroid distances between fibers or voids (like objects only)
def nearest_neighbor(objects, prefix):
    if len(objects) < 2:
        return{f"{prefix}_centroid_mean_um": np.nan, f"{prefix}_centroid_std_um": np.nan, f"{prefix}_centroid_min_um": np.nan}
    coordinates = objects[["centroid_X_um", "centroid_Y_um"]].to_numpy()
    distances, _ = cKDTree(coordinates).query(coordinates, k = 2)
    nearest = distances[:, 1]
    return {f"{prefix}_centroid_mean_um": float(np.mean(nearest)), f"{prefix}_centroid_std_um": float(np.std(nearest, ddof = 1)), f"{prefix}_centroid_min_um": float(np.min(nearest))}

# Centroid to centroid between unlike objects
def unlike_nearest_neighbor(fibers, voids):
    if fibers.empty or voids.empty:
        return{"fiber_to_void_centroid_mean_um": np.nan, "fiber_to_void_centroid_min_um": np.nan}
    fiber_coordinates = fibers[["centroid_X_um", "centroid_Y_um"]].to_numpy()
    void_coordinates = voids[["centroid_X_um", "centroid_Y_um"]].to_numpy()
    distances, _ = cKDTree(void_coordinates).query(fiber_coordinates, k = 1)
    return{"fiber_to_void_centroid_mean_um": float(np.mean(distances)), "fiber_to_void_centroid_min_um": float(np.min(distances))}
## ========================================== ##

## ========================================== ##
# 8. Visual Validation
# Create a diagnostic image to visually validate fiber and void placement
def visual_overlay(mask, output_path):
    overlay = np.zeros((*mask.shape, 3), dtype = float)
    overlay[mask == 255] = [1.0, 0.15, 0.15] # Fibers, Red
    overlay[mask == 120] = [0.65, 0.65, 0.65] # Matrix, Grey
    overlay[mask == 0] = [0.15, 0.15, 1.0] # Voids, Blue
    
    fig, ax = plt.subplots(figsize = (8,8))
    ax.imshow(overlay, interpolation = "nearest")
    ax.set_title("Microstructure Phase Overlay")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi = 250, bbox_inches = "tight",)
    plt.close(fig)
## ========================================== ##

## ========================================== ##
# 9. Characterize Subimage
def characterize_subimage(image_path, output_directory, pixel_size_um, min_area_px = 3, split_touching_fibers = True,):
    image_path = Path(image_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents = True, exist_ok = True)

    mask = read_mask(image_path)
    phases = define_phase(mask)
    height_px, width_px = mask.shape
    phase_table, image_area_um2 = phase_summary(mask, pixel_size_um)

    fibers = measure_objects(phases["fiber"], phase_name = "fiber", pixel_size_um = pixel_size_um, min_area_px = min_area_px, split_touching = split_touching_fibers)
    voids = measure_objects(phases["void"], phase_name = "void", pixel_size_um = pixel_size_um, min_area_px = min_area_px, split_touching = False)
    objects = pd.concat([fibers, voids], ignore_index = True)
    if not objects.empty:
        objects.insert(0, "subimage_id", image_path.stem)
    phase_table.insert(0, "subimage_id", image_path.stem)
    phase_fraction = dict(zip(phase_table["phase"], phase_table["area_fraction"]))

    summary = {"subimage_id": image_path.stem, "source_file": image_path.name, "image_width_px": int(width_px), "image_height_px": int(height_px), "pixel_size_um": float(pixel_size_um), 
               "image_area_um2": float(image_area_um2), "fiber_area_fraction": phase_fraction.get("fiber", np.nan), "matrix_area_fraction": phase_fraction.get("matrix", np.nan), 
               "void_area_fraction": phase_fraction.get("void", np.nan)}
    summary.update(nearest_neighbor(fibers, "fiber"))
    summary.update(nearest_neighbor(voids, "void"))
    summary.update(unlike_nearest_neighbor(fibers, voids))

    summary.update(summarize(fibers, "fiber"))
    summary.update(summarize(voids, "void"))

    pd.DataFrame([summary]).to_csv(output_directory/f"{image_path.stem}_summary.csv", index = False)
    objects.to_csv(output_directory/f"{image_path.stem}_objects.csv", index = False)
    phase_table.to_csv(output_directory/f"{image_path.stem}_phases.csv", index = False)

    visual_overlay(mask, output_directory/f"{image_path.stem}_overlay.png")
    return summary, objects, phase_table
## ========================================== ##

## ========================================== ##
# 10. CHaracterize all Subimages
def characterize_subimages(subimage_directory, output_directory, pixel_size_um, min_area_px = minimum_object_size, split_touching_fibers = True, min_distance = minimum_object_distance):
    subimage_directory = Path(subimage_directory)
    output_directory = Path(output_directory)
    if not subimage_directory.is_dir():
        raise FileNotFoundError(f"Subimage directory cannot be found here")
    if pixel_size_um <= 0:
        raise ValueError(f"Pixel to um conversion is not positive")
    image_extensions = {".tif", ".tiff", ".png", ".bmp"}
    image_paths = sorted(path for path in subimage_directory.rglob("*") if path.is_file() and path.suffix.lower() in image_extensions)
    if not image_paths:
        raise FileNotFoundError(f"No subimage files found in directory")
    output_directory.mkdir(parents = True, exist_ok = True,)

    all_summaries = []
    all_objects = []
    all_phases = []

    logging.info("Found %d candidate subimages in %s", len(image_paths), subimage_directory,)
    for image_path in image_paths:
        relative_path = image_path.relative_to(subimage_directory)
        result_folder = (output_directory / relative_path.parent)
        logging.info("Characterizing %s", relative_path,)
        # summary, objects, phases = characterize_subimage(image_path = image_path, output_directory = result_folder, pixel_size_um = pixel_size_um, min_area_px = min_area_px, split_touching_fibers = split_touching_fibers, min_distance = min_distance,)
        summary, objects, phases = characterize_subimage(image_path = image_path, output_directory = result_folder, pixel_size_um = pixel_size_um, min_area_px = min_area_px, split_touching_fibers = split_touching_fibers)
        summary["relative_image_path"] = str(relative_path)
        if not objects.empty:
            objects["relative_image_path"] = str(relative_path)
            all_objects.append(objects)
        phases["relative_image_path"] = str(relative_path)
        all_phases.append(phases)
        all_summaries.append(summary)
    summary_df = pd.DataFrame(all_summaries)
    summary_df.to_csv(output_directory / "all_image_summaries.csv", index = False)

    combined_objects = (pd.concat(all_objects, ignore_index = True) if all_objects else pd.DataFrame())
    combined_objects.to_csv(output_directory / "all_object_measurements.csv", index = False,)
    combined_phases = pd.concat(all_phases, ignore_index = True,)
    combined_phases.to_csv(output_directory / "all_phase_fractions.csv", index = False,)

    logging.info("Characterization complete. Processed %d subimages", len(all_summaries),)
    return summary_df