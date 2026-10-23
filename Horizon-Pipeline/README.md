# Horizon Pipeline

A Python package for processing and cleaning biomarker data from the PerkinElmer Horizon multiplex imaging analysis system.

## Overview

The Horizon Pipeline automates the extraction, validation, and standardization of biomarker intensity data from Horizon CSV exports. It handles encoding issues, matches sample files to sample identifiers, normalizes column names, filters for relevant biomarkers, calculates tissue areas, and outputs cleaned data ready for downstream analysis. Additionally, it computes phenotype counts, densities, and percentages based on biomarker expression thresholds defined in the orientation file.

## Features

- **Robust Data Import**: Reads CSV exports from Horizon analysis system with automatic encoding detection and error handling
- **Sample Matching**: Fuzzy matches sample file names to sample identifiers from orientation file
- **Column Standardization**: Converts raw Horizon column names to clean, standardized format (e.g., "Cell CD14 Mean Intensity")
- **Biomarker Filtering**: Selects only biomarker columns specified in orientation file with validation
- **Area Calculation**: Computes tissue sample area from ROI annotations, subtracts exclusion regions, and handles missing data
- **Data Validation**: Detects duplicate columns, missing values, and malformed data with clear error messages
- **Metadata Preservation**: Maintains sample names, spatial coordinates (X/Y position), class information, and calculated areas
- **Batch Processing**: Processes entire folders of CSV files in a single command
- **Metrics Computation**: Calculates phenotype counts, cell densities, and percentages based on biomarker thresholds

## Installation

### Prerequisites

- Python 3.7+
- pip or conda package manager

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd "Horizon Pipeline"
```

2. Install the package in development mode:

```bash
pip install -e .
```

3. Install required dependencies:

```bash
pip install pandas openpyxl
```

## Quick Start with Test Data

Try the pipeline immediately using the included test data:

```bash
python run_pipeline.py -i "test data/example Horizon exports" -o "test data/Orientation File.xlsx" -out "test data/results"
```

This will process the example CSV files and generate cleaned output in the `test data/results` folder.

## Usage

### Command Line Interface (CLI)

Run the pipeline from the command line with required arguments:

```bash
python run_pipeline.py -i INPUT_FOLDER -o ORIENTATION_FILE -out OUTPUT_FOLDER
```

**Required Arguments:**

- `-i, --input-folder`: Path to folder containing input CSV files to process
- `-o, --orientation-file`: Path to orientation Excel file defining biomarkers and cellular compartments
- `-out, --output-folder`: Path to output folder for cleaned CSV files and results

**Examples:**

Using the included test data:

```bash
python run_pipeline.py -i "test data/example Horizon exports" -o "test data/Orientation File.xlsx" -out "test data/results"
```

Basic usage:

```bash
python run_pipeline.py -i "E:\Data\Raw CSV Files" -o "E:\Data\MMP Orientation File.xlsx" -out "E:\Data\Cleaned Results"
```

Using relative paths:

```bash
python run_pipeline.py -i ./data/raw -o ./config/orientation.xlsx -out ./data/cleaned
```

Using full flag names:

```bash
python run_pipeline.py --input-folder "path/to/input" --orientation-file "path/to/orientation.xlsx" --output-folder "path/to/output"
```

### Programmatic Usage

Use the pipeline in your own Python code:

```python
from horizon_pipeline.cleaning.sample_cleaner import clean_all_samples
from horizon_pipeline.summary_extraction.metrics_pipeline import run_metrics_pipeline

# Clean the raw data
clean_all_samples(
    input_folder="path/to/input",
    orientation_file="path/to/orientation.xlsx",
    output_folder="path/to/output"
)

# Compute metrics on cleaned data
run_metrics_pipeline(
    orientation_path="path/to/orientation.xlsx",
    cleaned_csv_folder="path/to/output",
    output_folder="path/to/output"
)
```

## Input File Formats

### CSV Input Files

- **Format**: Standard CSV (comma-separated values)
- **Source**: Exported directly from PerkinElmer Horizon software
- **Expected Columns**: Biomarker columns (e.g., "Nuclei/Mean Intensity (FOXP3...)"), position columns, area annotations
- **Encoding**: Handles latin1 encoding automatically

### Orientation File (Excel)

- **Format**: .xlsx Excel file with columns:
  - `biomarkers`: Biomarker names (e.g., FOXP3, CD8, CD31)
  - `compartment`: Cellular compartment (Nuclei, Cell, Cytoplasm)
  - `sample_name`: Sample identifiers for matching
  - `phenotypes`: Phenotype definitions based on biomarker expression thresholds
  - `percentage_rules`: Rules for calculating percentages of cell populations
- **Purpose**: Defines which biomarkers to extract, their expected cellular locations, phenotype classifications, and percentage calculations

## Test Data

The repository includes example data for testing and demonstration:

- **`test data/example Horizon exports/`**: Contains 2 sample CSV files exported from the Horizon system
  - `Sample-01_feature_table.csv`: Example data with biomarker measurements
  - `Sample-02_feature_table.csv`: Additional sample data
- **`test data/Orientation File.xlsx`**: Example orientation file defining:
  - Biomarkers: FOXP3, CD8, CD31, etc.
  - Compartments: Nuclei, Cell, Cytoplasm
  - Sample names for matching

Use this data to verify the pipeline works correctly before processing your own files.

## Output Files

The pipeline generates the following files in the output folder:

1. **`<sample_name>.csv`** (one per sample)
   - Cleaned data with standardized column names
   - Only includes biomarker columns specified in orientation file
   - Includes X/Y position coordinates and sample metadata
   - Exclusion rows removed

2. **`sample_areas.csv`**
   - Summary of calculated tissue area for each sample
   - Columns: `sample_name`, `area` (in μm²)

3. **`summary/metrics_output.xlsx`**
   - Excel file with three sheets:
     - **Counts**: Phenotype counts per sample
     - **Densities**: Cell densities per mm² per sample
     - **Percentages**: Percentage distributions based on defined rules

## Processing Steps

The pipeline performs the following operations in sequence:

1. **Load Orientation File**: Reads Excel orientation file and normalizes column names
2. **Sample Matching**: Matches raw CSV filenames to sample identifiers using fuzzy string matching
3. **Encoding Fixes**: Handles BOM markers and special Unicode characters (μ, ²)
4. **Column Name Parsing**: Parses raw Horizon column names using regex patterns
5. **Column Standardization**: Converts to format: `{Compartment} {Biomarker} {Measurement}`
6. **Area Calculation**: Computes sample area from ROI annotations, subtracts exclusions
7. **Data Filtering**: Removes exclusion rows and biomarkers not in orientation file
8. **Position Filtering**: Removes rows without valid X/Y coordinates
9. **Compartment Validation**: Verifies biomarkers are in expected cellular compartments
10. **Output Cleaned Data**: Saves cleaned CSVs and area summary
11. **Phenotype Counting**: Classifies cells into phenotypes based on biomarker thresholds
12. **Density Calculation**: Computes cell densities per unit area
13. **Percentage Calculation**: Calculates population percentages using defined rules
14. **Metrics Output**: Saves counts, densities, and percentages to Excel file

## Project Structure

```
Horizon Pipeline/
├── pyproject.toml              # Project metadata and build configuration
├── README.md                   # This file
├── run_pipeline.py             # CLI entry point
├── test data/                  # Example data for testing and demonstration
│   ├── example Horizon exports/  # Sample CSV files from Horizon system
│   │   ├── 20250827_162229_2_fDZgre_Test Panel_Sample-02_feature_table.csv
│   │   └── 20251127_142934_1_85sTCm_Test Panel_Sample-01_feature_table.csv
│   └── Orientation File.xlsx   # Example orientation file with biomarker definitions
├── src/
│   └── horizon_pipeline/
│       ├── __init__.py
│       ├── cleaning/
│       │   ├── __init__.py
│       │   ├── sample_cleaner.py           # Main pipeline orchestrator
│       │   ├── file_matching.py            # Sample name matching logic
│       │   ├── clean_column_names.py       # Column name standardization
│       │   ├── select_biomarker_columns.py # Biomarker filtering and validation
│       │   └── calculate_sample_area.py    # Area calculation from annotations
│       ├── io/
│       │   ├── __init__.py
│       │   └── orientation_reader.py       # Orientation file reader
│       └── summary_extraction/
│           ├── __init__.py
│           ├── metrics_pipeline.py         # Metrics computation orchestrator
│           ├── phenotype_counter.py        # Phenotype classification logic
│           ├── density_calculator.py       # Density calculations
│           └── percentage_calculator.py    # Percentage calculations
└── horizon_pipeline.egg-info/  # Package metadata (auto-generated)
```

## Module Documentation

### `sample_cleaner.py`

Main orchestrator module that coordinates all cleaning steps.

**Key Function:**

- `clean_all_samples(input_folder, orientation_file, output_folder)`: Processes all CSV files in input folder

### `file_matching.py`

Implements fuzzy string matching to map CSV filenames to sample identifiers.

**Key Function:**

- `match_sample_name(file_stem, sample_names)`: Returns best matching sample name

### `clean_column_names.py`

Parses raw Horizon column names and standardizes them.

**Key Function:**

- `clean_column_names(df, biomarkers, filename)`: Returns DataFrame with standardized column names

### `select_biomarker_columns.py`

Filters columns to keep only specified biomarkers with compartment validation.

**Key Function:**

- `select_biomarker_columns(df, biomarker_to_compartment)`: Returns DataFrame with selected columns

### `calculate_sample_area.py`

Calculates tissue sample area from annotation rows.

**Key Function:**

- `calculate_sample_area(df)`: Returns total area in μm²

### `orientation_reader.py`

Reads and normalizes orientation Excel file.

**Key Function:**

- `load_orientation_file(path)`: Returns normalized DataFrame

## Dependencies

Core dependencies:

- `pandas>=1.0.0` - Data manipulation and CSV/Excel I/O
- `openpyxl>=3.0.0` - Excel file reading (.xlsx format)

Development dependencies:

- `pytest` - Testing framework (recommended)
- `black` - Code formatting (recommended)

## Error Handling

The pipeline validates input data and provides clear error messages for:

- Missing input or orientation files
- Duplicate column names (before and after cleaning)
- Missing required columns (biomarkers, compartment, sample_name)
- Encoding issues with special characters
- Malformed CSV files
- Biomarker compartment mismatches

## Performance Notes

- **Memory**: Processes one CSV file at a time; memory usage scales with CSV file size
- **Speed**: Typical processing time is 1-10 seconds per file depending on number of rows/columns
- **Batch Processing**: Can process hundreds of files in a single pipeline run

## Troubleshooting

### FileNotFoundError: Input folder does not exist

Check that the input folder path is correct and the folder exists on disk.

### ValueError: Duplicate column names

The CSV file has duplicate columns or the cleaning process creates duplicates. Check the input CSV for malformed data.

### No match found for file

The CSV filename doesn't contain any sample identifiers from the orientation file. Verify sample names match the CSV filenames.

### Missing required columns in orientation file

Ensure the Excel orientation file has columns named "biomarkers", "compartment", and "sample_name".

### Version 0.1.0

- Initial release
- Support for Horizon CSV exports
- Column standardization pipeline
- Biomarker filtering and validation
- CLI interface
