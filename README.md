# zeolite-particle-analysis

Automated SEM particle size analysis for zeolite-doped optical films.

## Overview

This script performs quantitative image analysis on scanning electron microscopy (SEM) images to extract particle size distributions, 
morphological statistics, and publication-quality visualizations. Designed for reproducible supplementary analysis in peer-reviewed manuscripts.

**Author:** Nasrettin Yunus  

---

## Features

✓ **Automated segmentation** via Otsu thresholding, morphological filtering, and watershed  
✓ **Morphometric analysis** — equivalent circle diameter (ECD), aspect ratio, area, solidity  
✓ **Statistical summary** — mean, SD, 95% CI, percentiles (d₁₀, d₅₀, d₉₀)  
✓ **Publication-quality histogram** with KDE overlay and ±1 SD band  
✓ **Quality control overlay** showing all detected particles  
✓ **Reproducible export** — CSV particle table + JSON statistics  
✓ **Flexible input** — file or clipboard image  

---

## Installation

### Requirements
- Python 3.9+
- pip

### Setup

```bash
# Clone repository
git clone https://github.com/NasretYunus/zeolite-particle-analysis.git
cd zeolite-particle-analysis

# Install dependencies
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python scikit-image matplotlib scipy numpy pandas pillow
```

---

## Usage

### Basic usage (file input)
```bash
python sem_particle_analysis.py --image Fig_2b.png \
    --scale_bar_px 412 \
    --scale_bar_um 5 \
    --output results/
```

### From clipboard
Copy an SEM image to your clipboard, then:
```bash
python sem_particle_analysis.py --clipboard \
    --scale_bar_px 412 \
    --scale_bar_um 5 \
    --output results/
```

### Command-line arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--image` | str | None | Path to SEM image (PNG/TIFF/BMP) |
| `--clipboard` | flag | — | Load image from clipboard instead |
| `--scale_bar_px` | float | 412 | Scale bar length in pixels |
| `--scale_bar_um` | float | 5.0 | Scale bar physical length (µm) |
| `--output` | str | `results/` | Output directory |

---

## Output Files

| File | Description |
|------|-------------|
| `{stem}_particles.csv` | One row per detected particle with morphometry |
| `{stem}_statistics.json` | Descriptive statistics (N, mean, SD, CI, percentiles) |
| `{stem}_histogram.png` | distribution plot (800 DPI) |
| `{stem}_overlay.png` | Quality control visualization of detections |

### Example CSV structure
```
label,area_um2,ecd_um,major_axis_um,minor_axis_um,aspect_ratio,eccentricity,solidity,centroid_row,centroid_col
1,0.2156,0.5239,0.6891,0.4127,1.6686,0.7145,0.8923,245,187
2,0.1847,0.4843,0.5834,0.3985,1.4634,0.6521,0.9112,456,312
...
```

### Example JSON structure
```json
{
  "N": 24,
  "mean_um": 0.572,
  "median_um": 0.463,
  "std_um": 0.246,
  "sem_um": 0.05,
  "min_um": 0.339,
  "max_um": 1.235,
  "ci95_low": 0.469,
  "ci95_high": 0.676,
  "d10_um": 0.37,
  "d50_um": 0.463,
  "d90_um": 0.939
}
```

---

## Configuration

Edit defaults in `sem_particle_analysis.py` (section 1):

```python
DEFAULT_SCALE_BAR_PX = 412      # length of scale bar in pixels
DEFAULT_SCALE_BAR_UM = 5.0      # physical length of scale bar (µm)
MIN_PARTICLE_AREA_UM2 = 0.05    # discard objects smaller than this (µm²)
MAX_PARTICLE_AREA_UM2 = 50.0    # discard objects larger than this (µm²)
HISTOGRAM_BINS = 20             # number of bins in histogram
DPI = 800                       # figure resolution
```

---

## Example Results

Input: Fig. 2b (intermediate magnification SEM)  
Scale: 5 µm

```
Particles detected: 24
Mean ECD: 0.572 ± 0.246 µm (mean ± SD)
Range: 0.339–1.235 µm
95% CI: [0.469, 0.676] µm
```

---

## Method

### Segmentation pipeline
1. **CLAHE contrast enhancement** — improves particle visibility
2. **Gaussian blur** — reduces sensor noise
3. **Otsu thresholding** — automated binary segmentation
4. **Morphological filtering** — removes noise specks and fills holes
5. **Watershed algorithm** — splits touching particles

### Morphometric features
- **Equivalent Circle Diameter (ECD)** = 2√(Area/π)
- **Aspect Ratio** = Major Axis / Minor Axis
- **Solidity** = Area / Convex Hull Area
- **Eccentricity** — deviation from circular shape

---

## Limitations

- **Scale calibration critical** — incorrect scale bar px/µm will invalidate all results
- **Binary thresholding** — works best on SEM images with clear particle contrast
- **Touching particles** — watershed may over-segment or under-segment depending on morphology
- **Noise particles** — min/max area filters help but manual review of overlay recommended

---

## Quality Control

Always inspect the `{stem}_overlay.png` to verify:
- Particles correctly detected (not missed or over-segmented)
- No large artifacts included
- Scale bar correctly positioned

If segmentation is poor, adjust:
- `--scale_bar_px` and `--scale_bar_um` (verify from image metadata)
- `MIN_PARTICLE_AREA_UM2` / `MAX_PARTICLE_AREA_UM2` in config

---

## Citation

If you use this code, please cite:

```bibtex
@software{yunus2026zeolite,
  title={Zeolite Particle Analysis: Automated SEM Image Segmentation},
  author={Yunus, Nasrettin},
  year={2026},
  url={https://github.com/NasretYunus/zeolite-particle-analysis}
}
```

---

## License

MIT License — see LICENSE file

---

## Author

**Nasrettin Yunus**  

## Support

For issues or questions, open a GitHub issue or contact the author.
