import pandas as pd
from pathlib import Path

from horizon_pipeline.io.orientation_reader import load_orientation_file
from horizon_pipeline.cleaning.file_matching import match_sample_name
from horizon_pipeline.cleaning.clean_column_names import clean_column_names
from horizon_pipeline.cleaning.select_biomarker_columns import select_biomarker_columns
from horizon_pipeline.cleaning.calculate_sample_area import calculate_sample_area


def clean_all_samples(input_folder, orientation_file, output_folder):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load orientation file
    orient = load_orientation_file(orientation_file)
    biomarker_to_compartment = dict(
        zip(orient["biomarkers"], orient["compartment"])
    )

    sample_names = (
        orient["sample_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    # Prepare summary collectors
    combined_rows = []
    area_summary = []

    # Process each CSV in the input folder
    for file in input_path.glob("*.csv"):
        raw_stem = file.stem
        sample_name = match_sample_name(raw_stem, sample_names)

        if sample_name is None:
            print(f"No match found for file: {file.name}")
            continue

        # Biomarkers for this sample
        # Flatten list-of-lists into a single list of biomarker names
        biomarkers = (
            orient["biomarkers"]
            .dropna()
            .explode()        # turns lists into rows
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
)


        # Load and clean the CSV
        try:
            df = pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file, encoding="latin1")
    

        # Remove BOM and whitespace
        df.columns = df.columns.str.replace("\ufeff", "", regex=False)
        df.columns = df.columns.str.strip()
       

        area = calculate_sample_area(df)
        df = clean_column_names(df, biomarkers, file)
        
        # Remove rows containing "exclusion" anywhere
        exclusion_mask = df.apply(
            lambda row: row.astype(str).str.contains("exclusion", case=False)
        ).any(axis=1)
        df = df[~exclusion_mask]

        # Select biomarker columns + required extras
        df = select_biomarker_columns(
            df,
            biomarker_to_compartment
        )
    
        df = df.dropna(subset=["X Position"])
        # Add metadata
        df["sample_name"] = sample_name
        df["sample_area"] = area

        # Save cleaned file
        cleaned_name = f"{sample_name}.csv"
        df.to_csv(output_path / cleaned_name, index=False, encoding="utf-8-sig")

        # Add to combined structures
        combined_rows.append(df)
        area_summary.append({"sample_name": sample_name, "area": area})


    # Save area summary
    area_folder = output_path / "area"
    area_folder.mkdir(exist_ok=True)

    area_df = pd.DataFrame(area_summary)
    area_df.to_csv(area_folder / "sample_areas.csv", index=False)


    return {
        "areas": output_path / "sample_areas.csv"
    }