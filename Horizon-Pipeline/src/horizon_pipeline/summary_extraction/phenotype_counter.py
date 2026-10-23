import os
import pandas as pd
import re
from pyparsing import col

def find_threshold_column(df, marker):
    """
    Finds the correct threshold column for a given marker.
    Matches whole marker names only, not substrings.
    """
    marker = marker.lower()

    for col in df.columns:
        col_lower = col.lower()

        # Must contain "threshold"
        if "threshold" not in col_lower:
            continue

        # Remove the word "threshold" and split on spaces
        # Example: "Cell CD14 Threshold" -> ["cell", "cd14"]
        parts = col_lower.replace("threshold", "").strip().split()

        # Look for exact match
        if marker in parts:
            return col

    return None

def parse_phenotype_rule(rule, biomarker_list):
    """
    Parse a phenotype rule using the known biomarker names.
    Example:
        CD68+CD16-CD14+  → [('CD68', True), ('CD16', False), ('CD14', True)]
    """

    # Sort biomarkers by length (longest first) so PD-L1 is matched before PD
    biomarkers_sorted = sorted(biomarker_list, key=len, reverse=True)

    parsed = []
    i = 0

    while i < len(rule):
        matched = False

        for marker in biomarkers_sorted:
            if rule.startswith(marker, i):
                # Next character must be + or -
                sign = rule[i + len(marker)]
                parsed.append((marker, sign == "+"))
                i += len(marker) + 1
                matched = True
                break

        if not matched:
            raise ValueError(f"Could not parse phenotype rule at position {i}: {rule}")

    return parsed



def count_cells_for_phenotype(df, rule, biomarker_list):

    # Special case: Total Cells
    if rule.strip().lower() == "total cells":
        return len(df)

    parsed = parse_phenotype_rule(rule, biomarker_list)
    print("RULE:", rule, "→ PARSED:", parsed)

    mask = pd.Series([True] * len(df))

    for marker, is_positive in parsed:
        col = find_threshold_column(df, marker)
        if col is None:
            return 0

        mask &= (df[col] == is_positive)

    return mask.sum()


def count_phenotypes_in_folder(folder_path, phenotype_list, biomarker_list):
    results = {}

    for file in os.listdir(folder_path):
        if not file.lower().endswith(".csv"):
            continue

        sample_name = os.path.splitext(file)[0]
        df = pd.read_csv(os.path.join(folder_path, file))

        sample_counts = {}

        for phenotype in phenotype_list:
            sample_counts[phenotype] = count_cells_for_phenotype(
                df, phenotype, biomarker_list
            )

        results[sample_name] = sample_counts

    return results