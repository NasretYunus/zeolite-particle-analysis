"""
SEM Particle Size Analysis 
================================================
Manuscript: Symmetry Breaking in Optical Backlighting: A Comparative T-Matrix and Mie Analysis of Polarization Discrimination in Spheroidal Zeolite-
Doped Films
Authors:    Nasrettin Yunus 
Journal:    Optics Communications
GitHub:     https://github.com/NasretYunus/sem-particle-analysis

Description
-----------
This script performs automated particle size analysis on SEM images.
It segments individual particles, extracts morphological statistics
(equivalent diameter, aspect ratio, area), generates a publication-quality
histogram, and exports all results to CSV for reproducibility.

Requirements
------------
    pip install opencv-python scikit-image matplotlib scipy numpy pandas pillow

Usage
-----
    # From file:
    python sem_particle_analysis.py --image path/to/sem_image.png \
                                    --scale_bar_px 412 \
                                    --scale_bar_um 5 \
                                    --output results/

    # From clipboard:
    python sem_particle_analysis.py --clipboard \
                                    --scale_bar_px 412 \
                                    --scale_bar_um 5 \
                                    --output results/

Tested on Python 3.9+

License: MIT
"""
import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import ImageGrab
from scipy import ndimage, stats
from matplotlib.ticker import FuncFormatter
from skimage import filters, measure, morphology, segmentation
from skimage.color import label2rgb

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 1.  CONFIGURATION  (edit defaults here)
# ─────────────────────────────────────────────
DEFAULT_SCALE_BAR_PX = 412      # length of scale bar in pixels
DEFAULT_SCALE_BAR_UM = 5.0      # physical length of scale bar (µm)
MIN_PARTICLE_AREA_UM2 = 0.05    # discard objects smaller than this (µm²)
MAX_PARTICLE_AREA_UM2 = 50.0    # discard objects larger than this (µm²)
HISTOGRAM_BINS = 20             # number of bins in the size histogram

# Publication-quality plot settings
FONT_SIZE = 11
DPI = 800
FIG_WIDTH = 8   # inches


# ─────────────────────────────────────────────
# 2.  SCALE CALIBRATION
# ─────────────────────────────────────────────
def get_pixel_size(scale_bar_px: float, scale_bar_um: float) -> float:
    """Return physical size of one pixel in µm."""
    return scale_bar_um / scale_bar_px


# ─────────────────────────────────────────────
# 3.  IMAGE PRE-PROCESSING
# ─────────────────────────────────────────────
def preprocess(image_path: str) -> np.ndarray:
    """
    Load a grayscale SEM image and apply:
      - CLAHE contrast enhancement
      - Gaussian smoothing
    Returns uint8 grayscale array.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    # Adaptive histogram equalisation
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img = clahe.apply(img)

    # Mild Gaussian blur to reduce sensor noise
    img = cv2.GaussianBlur(img, (3, 3), 0)
    return img


# ─────────────────────────────────────────────
# 4.  SEGMENTATION
# ─────────────────────────────────────────────
def segment_particles(gray: np.ndarray) -> np.ndarray:
    """
    Segment bright particles from the SEM background using:
      1. Otsu thresholding on the top histogram peak
      2. Morphological opening to remove noise specks
      3. Watershed to split touching particles

    Returns an integer label array (0 = background).
    """
    # --- Threshold ---
    thresh = filters.threshold_otsu(gray)
    binary = gray > thresh

    # --- Clean small noise ---
    binary = morphology.remove_small_objects(binary, min_size=10)
    binary = morphology.remove_small_holes(binary, area_threshold=50)
    binary = morphology.binary_opening(binary, morphology.disk(2))

    # --- Distance transform + watershed to split touching blobs ---
    distance = ndimage.distance_transform_edt(binary)
    coords = morphology.local_maxima(distance, indices=True)
    mask = np.zeros(distance.shape, dtype=bool)
    mask[tuple(coords)] = True
    markers, _ = ndimage.label(mask)
    labels = segmentation.watershed(-distance, markers, mask=binary)

    return labels


# ─────────────────────────────────────────────
# 5.  FEATURE EXTRACTION
# ─────────────────────────────────────────────
def extract_features(labels: np.ndarray,
                     px_size_um: float,
                     min_area: float,
                     max_area: float) -> pd.DataFrame:
    """
    Measure region properties and convert pixel measurements to µm.
    Returns a DataFrame with one row per valid particle.
    """
    props = measure.regionprops(labels)
    records = []

    for p in props:
        area_um2 = p.area * px_size_um ** 2
        if not (min_area <= area_um2 <= max_area):
            continue  # filter noise and artefacts

        # Equivalent circle diameter (ECD) = diameter of a circle with same area
        ecd_um = 2.0 * np.sqrt(area_um2 / np.pi)

        # Major / minor axes
        major_um = p.major_axis_length * px_size_um
        minor_um = p.minor_axis_length * px_size_um
        aspect   = major_um / minor_um if minor_um > 0 else np.nan

        records.append({
            "label":          p.label,
            "area_um2":       round(area_um2, 4),
            "ecd_um":         round(ecd_um, 4),
            "major_axis_um":  round(major_um, 4),
            "minor_axis_um":  round(minor_um, 4),
            "aspect_ratio":   round(aspect, 4),
            "eccentricity":   round(p.eccentricity, 4),
            "solidity":       round(p.solidity, 4),
            "centroid_row":   int(p.centroid[0]),
            "centroid_col":   int(p.centroid[1]),
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# 6.  STATISTICS SUMMARY
# ─────────────────────────────────────────────
def compute_statistics(df: pd.DataFrame) -> dict:
    """Return a dict of descriptive statistics for ECD (µm)."""
    d = df["ecd_um"]
    ci_low, ci_high = stats.t.interval(
        confidence=0.95,
        df=len(d) - 1,
        loc=d.mean(),
        scale=stats.sem(d)
    )
    return {
        "N":          len(d),
        "mean_um":    round(d.mean(), 3),
        "median_um":  round(d.median(), 3),
        "std_um":     round(d.std(ddof=1), 3),
        "sem_um":     round(stats.sem(d), 3),
        "min_um":     round(d.min(), 3),
        "max_um":     round(d.max(), 3),
        "ci95_low":   round(ci_low, 3),
        "ci95_high":  round(ci_high, 3),
        "d10_um":     round(np.percentile(d, 10), 3),
        "d50_um":     round(np.percentile(d, 50), 3),
        "d90_um":     round(np.percentile(d, 90), 3),
    }


# ─────────────────────────────────────────────
# 7.  PUBLICATION-QUALITY HISTOGRAM
# ─────────────────────────────────────────────
def plot_histogram(df: pd.DataFrame,
                   stat: dict,
                   output_path: str,
                   bins: int = HISTOGRAM_BINS) -> None:
    """
    Draw a publication-ready particle size histogram with:
      - Relative frequency (normalised count) on y-axis
      - KDE overlay
      - Mean ± SD vertical lines
      - Statistics text box
    """
    sizes = df["ecd_um"].values

    plt.rcParams.update({
        "font.family": "serif",
        "font.size":   FONT_SIZE,
        "axes.linewidth": 1.2,
    })

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_WIDTH * 0.65))

    # --- Histogram (relative frequency) ---
    counts, bin_edges, patches = ax.hist(
        sizes,
        bins=bins,
        density=True,
        color="#4C72B0",
        edgecolor="white",
        linewidth=0.6,
        alpha=0.80,
        label="Particle count (normalised)",
        zorder=2
    )

    # --- KDE curve ---
    kde_x = np.linspace(sizes.min() - 0.3, sizes.max() + 0.3, 500)
    kde   = stats.gaussian_kde(sizes, bw_method="scott")
    ax.plot(kde_x, kde(kde_x), color="#C44E52", linewidth=2.0,
            label="KDE", zorder=3)

    # --- Mean line ---
    ax.axvline(stat["mean_um"], color="#2ca02c", linewidth=1.8,
               linestyle="--", zorder=4, label=f"Mean = {stat['mean_um']} µm")

    # --- Mean ± SD shaded band ---
    ax.axvspan(stat["mean_um"] - stat["std_um"],
               stat["mean_um"] + stat["std_um"],
               alpha=0.12, color="#2ca02c", zorder=1,
               label=f"±1 SD ({stat['std_um']} µm)")

    # --- Statistics text box ---
    textstr = (
        f"N  = {stat['N']}\n"
        f"Mean = {stat['mean_um']} µm\n"
        f"Median = {stat['median_um']} µm\n"
        f"SD   = {stat['std_um']} µm\n"
        f"Range = [{stat['min_um']}, {stat['max_um']}] µm\n"
        f"95% CI = [{stat['ci95_low']}, {stat['ci95_high']}] µm"
    )
    props_box = dict(boxstyle="round,pad=0.5", facecolor="wheat", alpha=0.6)
    ax.text(0.97, 0.97, textstr, transform=ax.transAxes,
            fontsize=FONT_SIZE - 1, verticalalignment="top",
            horizontalalignment="right", bbox=props_box, zorder=5)

    # --- Axes labels & formatting ---
    ax.set_xlabel("Equivalent Circle Diameter, ECD (µm)", fontsize=FONT_SIZE)
    ax.set_ylabel("Probability Density", fontsize=FONT_SIZE)
    #ax.set_title("Particle Size Distribution (SEM Analysis)", fontsize=FONT_SIZE + 1)
    ax.legend(fontsize=FONT_SIZE - 1, framealpha=0.7)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: "" if np.isclose(y, 0) else f"{y:g}"))
    ax.set_xlim(left=0)
    ax.grid(axis="y", linestyle=":", linewidth=0.7, alpha=0.7)
    ax.tick_params(direction="in", top=True, right=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [✓] Histogram saved     → {output_path}")


# ─────────────────────────────────────────────
# 8.  OVERLAY VISUALISATION (QC)
# ─────────────────────────────────────────────
def plot_overlay(gray: np.ndarray,
                 labels: np.ndarray,
                 df: pd.DataFrame,
                 output_path: str) -> None:
    """
    Save a colour-overlay QC image showing detected particles.
    """
    # Keep only validated particles
    valid_labels = set(df["label"].tolist())
    filtered = np.where(np.isin(labels, list(valid_labels)), labels, 0)

    overlay = label2rgb(filtered, image=gray, bg_label=0, alpha=0.35)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(overlay)
    ax.set_title(f"Detected Particles (N = {len(df)})", fontsize=FONT_SIZE)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [✓] Overlay saved       → {output_path}")


# ─────────────────────────────────────────────
# 9.  CLIPBOARD IMAGE HANDLER
# ─────────────────────────────────────────────
def load_from_clipboard() -> str:
    """
    Grab image from clipboard and save it temporarily.
    Returns the path to the saved image.
    """
    try:
        img = ImageGrab.grabclipboard()
        if img is None:
            raise ValueError("No image found in clipboard")
        
        temp_path = "temp_clipboard_image.png"
        img.convert("L").save(temp_path)  # Convert to grayscale PNG
        print(f"  [✓] Image loaded from clipboard → {temp_path}")
        return temp_path
    except Exception as e:
        print(f"  [!] Error loading clipboard image: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# 10.  MAIN PIPELINE
# ─────────────────────────────────────────────
def run_analysis(image_path: str,
                 scale_bar_px: float,
                 scale_bar_um: float,
                 output_dir: str) -> None:
    """
    Execute the complete analysis pipeline.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem = Path(image_path).stem

    print(f"\n{'='*60}")
    print(f"  SEM Particle Size Analysis")
    print(f"  Image : {image_path}")
    print(f"  Scale : {scale_bar_px} px = {scale_bar_um} µm "
          f"({get_pixel_size(scale_bar_px, scale_bar_um)*1000:.2f} nm/px)")
    print(f"{'='*60}\n")

    px_size = get_pixel_size(scale_bar_px, scale_bar_um)

    # --- Pre-process ---
    print("  [1/5] Pre-processing image …")
    gray = preprocess(image_path)

    # --- Segment ---
    print("  [2/5] Segmenting particles …")
    labels = segment_particles(gray)

    # --- Extract features ---
    print("  [3/5] Extracting features …")
    df = extract_features(labels, px_size,
                          MIN_PARTICLE_AREA_UM2,
                          MAX_PARTICLE_AREA_UM2)
    print(f"         → {len(df)} particles retained after filtering")

    if len(df) < 5:
        print("  [!] Too few particles detected. "
              "Check scale_bar_px / thresholding parameters.")
        sys.exit(1)

    # --- Statistics ---
    print("  [4/5] Computing statistics …")
    stat = compute_statistics(df)
    for k, v in stat.items():
        print(f"         {k:15s}: {v}")

    # --- Save CSV ---
    csv_path = os.path.join(output_dir, f"{stem}_particles.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n  [✓] Particle data saved  → {csv_path}")

    # --- Save statistics JSON ---
    stat_path = os.path.join(output_dir, f"{stem}_statistics.json")
    with open(stat_path, "w") as f:
        json.dump(stat, f, indent=2)
    print(f"  [✓] Statistics saved     → {stat_path}")

    # --- Histogram ---
    print("\n  [5/5] Generating figures …")
    hist_path = os.path.join(output_dir, f"{stem}_histogram.png")
    plot_histogram(df, stat, hist_path)

    # --- Overlay (QC) ---
    overlay_path = os.path.join(output_dir, f"{stem}_overlay.png")
    plot_overlay(gray, labels, df, overlay_path)

    print(f"\n{'='*60}")
    print(f"  ✓ Analysis complete.  Results in: {output_dir}")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────
# 11.  CLI ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SEM particle size analysis — supplementary code"
    )
    parser.add_argument("--image",         required=False, default=None,
                        help="Path to SEM image (PNG / TIFF / BMP)")
    parser.add_argument("--clipboard",     action="store_true",
                        help="Load image from clipboard instead")
    parser.add_argument("--scale_bar_px",  type=float,
                        default=DEFAULT_SCALE_BAR_PX,
                        help="Length of scale bar in pixels")
    parser.add_argument("--scale_bar_um",  type=float,
                        default=DEFAULT_SCALE_BAR_UM,
                        help="Physical length of scale bar in µm")
    parser.add_argument("--output",        default="results/",
                        help="Output directory for results")
    args = parser.parse_args()

    # Determine image source
    if args.clipboard:
        image_path = load_from_clipboard()
    elif args.image:
        image_path = args.image
    else:
        print("  [!] Provide --image or --clipboard flag")
        sys.exit(1)

    run_analysis(
        image_path    = image_path,
        scale_bar_px  = args.scale_bar_px,
        scale_bar_um  = args.scale_bar_um,
        output_dir    = args.output,
    )