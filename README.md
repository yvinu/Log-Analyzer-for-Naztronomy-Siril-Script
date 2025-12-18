# Naztronomy - Siril Script log analyzer

## Naztronomy-Smart_Telescope_PP.py

A scrpt to generate a cummary report on the outcomes of running the Naztronomy Python script for Smart telescopes.

**Features:**

Provides a summary of:
 - the time spent in each phase of preprocessing
 - the yield of key stages (conversion, registration, etc.)


## Installation

To install these scripts:

1. Place the Python `.py` files from this repository in your local Siril scripts directory

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

- **Vinu Yamunan**
- - **Nazmus Nasir** - [Naztronomy](https://www.naztronomy.com) for the underlying main python script


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

