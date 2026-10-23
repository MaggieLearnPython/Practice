import os
import pandas as pd
from pathlib import Path

from horizon_pipeline.io.orientation_reader import load_orientation_file
from horizon_pipeline.summary_extraction.phenotype_counter import count_phenotypes_in_folder
from horizon_pipeline.summary_extraction.density_calculator import calculate_densities
from horizon_pipeline.summary_extraction.percentage_calculator import calculate_percentages


def run_metrics_pipeline(orientation_path, cleaned_csv_folder, output_folder):
    print("\n=== Running Metrics Pipeline ===")

    # Create summary folder
    summary_folder = Path(output_folder) / "summary"
    summary_folder.mkdir(exist_ok=True)

    output_excel_path = summary_folder / "metrics_output.xlsx"

    
    # Load orientation file
    orientation = load_orientation_file(orientation_path)
    phenotypes = orientation.phenotypes
    biomarkers = orientation["biomarkers"].tolist()
    percentage_rules = orientation.percentage_rules

    # Count phenotypes
    counts = count_phenotypes_in_folder(cleaned_csv_folder, phenotypes, biomarkers)

    # Extract sample areas
    area_dict = {}
    for file in os.listdir(cleaned_csv_folder):
        if file.lower().endswith(".csv"):
            sample = os.path.splitext(file)[0]
            print("Reading:", os.path.join(cleaned_csv_folder, file))
            df = pd.read_csv(os.path.join(cleaned_csv_folder, file))
            area_dict[sample] = df["sample_area"].iloc[0]

    # Compute densities
    densities = calculate_densities(counts, area_dict)

    # Compute percentages
    percentages = calculate_percentages(counts, percentage_rules)

    # Write Excel output
    with pd.ExcelWriter(output_excel_path) as writer:
        pd.DataFrame.from_dict(counts, orient="index").to_excel(writer, sheet_name="Counts")
        pd.DataFrame.from_dict(densities, orient="index").to_excel(writer, sheet_name="Densities")
        pd.DataFrame.from_dict(percentages, orient="index").to_excel(writer, sheet_name="Percentages")

    print(f"\nMetrics complete. Output saved to:\n{output_excel_path}")


if __name__ == "__main__":
    print("\n=== Metrics Pipeline CLI ===")
    orientation_path = input("Enter orientation file path: ").strip()
    cleaned_folder = input("Enter folder containing cleaned CSVs: ").strip()
    output_folder = input("Enter output folder path: ").strip()

    run_metrics_pipeline(
        orientation_path,
        cleaned_folder,
        output_folder
    )
