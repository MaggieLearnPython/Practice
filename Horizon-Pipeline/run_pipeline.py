import argparse
from pathlib import Path

from horizon_pipeline.cleaning.sample_cleaner import clean_all_samples
from horizon_pipeline.summary_extraction.metrics_pipeline import run_metrics_pipeline



def main():
    parser = argparse.ArgumentParser(
        description="Horizon Pipeline - Clean samples and compute metrics"
    )

    parser.add_argument("-i", "--input-folder", required=True)
    parser.add_argument("-o", "--orientation-file", required=True)
    parser.add_argument("-out", "--output-folder", required=True)

    args = parser.parse_args()

    input_path = Path(args.input_folder)
    orientation_path = Path(args.orientation_file)
    output_path = Path(args.output_folder)

    if not input_path.exists():
        print(f"Error: Input folder does not exist: {input_path}")
        return 1

    if not orientation_path.exists():
        print(f"Error: Orientation file does not exist: {orientation_path}")
        return 1

    print("\n=== Running Full Pipeline ===")

    # Step 1: Clean samples
    clean_all_samples(
        input_folder=str(input_path),
        orientation_file=str(orientation_path),
        output_folder=str(output_path)
    )

    # Step 2: Run metrics on cleaned samples
    cleaned_csv_folder = output_path  # cleaner writes cleaned CSVs here

    run_metrics_pipeline(
        orientation_path=str(orientation_path),
        cleaned_csv_folder=str(cleaned_csv_folder),
        output_folder=str(output_path)
    )

    print("\nPipeline complete.")
    return 0


if __name__ == "__main__":
    exit(main())