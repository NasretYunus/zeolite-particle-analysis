# zeolite-particle-analysis

Automated SEM particle size analysis for zeolite-doped optical films.

## Overview

This script performs quantitative image analysis on scanning electron microscopy (SEM) images to extract particle size distributions, 
morphological statistics, and publication-quality visualizations. Designed for reproducible supplementary analysis in peer-reviewed manuscripts.

**Authors:** Ali Emre Yunus, Nasrettin Yunus  

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
## Input
- Image: Fig. 2(b) from manuscript
- Scale bar: 42 px = 5 µm (as measured from the embedded SEM scale bar)

## Usage
python sem_particle_analysis.py \
    --image Fig2b_input.png \
    --scale_bar_px 42 \
    --scale_bar_um 5 \
    --output results/

## Filter parameters
- MIN_PARTICLE_AREA_UM2 = 0.05 µm²
- MAX_PARTICLE_AREA_UM2 = 50.0 µm²

## Results (n = 52)
- Mean ECD:  1.483 µm
- SD:        1.178 µm
- Range:     0.484–7.679 µm
- 95% CI:    [1.155, 1.811] µm
- Median:    1.078 µm
- D10/D50/D90: 0.556 / 1.078 / 2.369 µm


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
  "N": 52,
  "mean_um": 1.483,
  "median_um": 1.078,
  "std_um": 1.178,
  "d10_um": 0.556,
  "d50_um": 1.078,
  "d90_um": 2.369
    .............
}


---

## Configuration

Edit defaults in `sem_particle_analysis.py` (section 1):

```python
DEFAULT_SCALE_BAR_PX = 42      # length of scale bar in pixels
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
  authors={Yunus, Ali Emre; Yunus, Nasrettin},
  year={2026},
  url={https://github.com/NasretYunus/zeolite-particle-analysis}
}
```

---

## License

MIT License — see LICENSE file

---

## Authors
**Ali Emre Yunus**  
**Nasrettin Yunus**  

## Support

For issues or questions, open a GitHub issue or contact the author.
