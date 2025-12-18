# Naztronomy - Siril Script log analyzer

## Naztronomy-Smart_Telescope_PP.py

A comprehensive Python script that automates the preprocessing workflow for smart telescopes, including file conversion, registration, stacking, and SPCC color calibration.

**Supported Telescopes:**

- ZWO Seestar S30
- ZWO Seestar S50
- Dwarf 2
- Dwarf 3
- Celestron Origin

**Features:**

- Automatic batching for large datasets (>2000 files on Windows)
- Optional calibration frame support (darks, flats, biases)
- Automatic master frame creation from calibration files
- Drizzle integration for improved resolution
- Background extraction and filtering options
- Spectrophotometric Color Calibration (SPCC)
- Save/Load presets functionality

**Demo Video:** [YouTube - Smart Telescope Processing](https://www.youtube.com/watch?v=6v0SHEe0ZJ8)

## Installation

Two ways to install these scripts:

1. Place the Python `.py` files from this repository in your local Siril scripts directory
2. Install directly through Siril by going to **Scripts >> Get Scripts** in Siril and searching for "Naztronomy"

## System Requirements

- Siril 1.3.6 or later
- Python packages: PyQt6, numpy, astropy (automatically installed by the scripts)
- Recommended: Blank working directory for clean setup

## Usage Guidelines

### For Smart Telescope Script:

- Must have a `lights` subdirectory in your working directory
- Calibration frames are optional but recommended
- Supports automatic batching for large datasets
- SPCC requires local Gaia catalog for best results

## Limitations

- **Windows File Limit:** The `.ssf` scripts do not work with file counts > 2048 on Windows
- **OSC Optimization:** Current scripts are optimized for OSC cameras (mono support is experimental)
- **Disk Space:** OSC script copies files before processing, requiring additional storage

## Authors

- **Nazmus Nasir** - [Naztronomy](https://www.naztronomy.com)
- **Vinu Yamunan** 


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

