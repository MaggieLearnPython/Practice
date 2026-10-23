import re
import pandas as pd

def select_biomarker_columns(df, biomarker_to_compartment):
    """
    biomarker_to_compartment: dict like {"FOXP3": "Nuclei", "CD31": "Cell", ...}
    """

    # Normalize keys for comparison
    biomarker_map = {k.lower(): v.title() for k, v in biomarker_to_compartment.items()}

    # Regex for cleaned biomarker columns
    pattern = re.compile(
        r"^(Nuclei|Cytoplasm|Cell)\s+([A-Za-z0-9_\-\u0370-\u03FF]+)\s+(Mean Intensity|Threshold)$"
    )

    keep_biomarker_cols = []
    for col in df.columns:
        m = pattern.match(col)
        if not m:
            continue

        comp = m.group(1)
        biomarker = m.group(2)

        biomarker_lc = biomarker.lower()

        # Skip biomarkers not in orientation file
        if biomarker_lc not in biomarker_map:
            continue

        # Check compartment match
        expected_comp = biomarker_map[biomarker_lc]
        if comp != expected_comp:
            continue

        keep_biomarker_cols.append(col)

    # --- KEEP EXTRA COLUMNS YOU WANT ---
    extra_cols = []

    # 1. Keep Class Group
    if "Class group" in df.columns:
        extra_cols.append("Class group")

    # 2. Keep and rename X/Y position columns
    rename_map = {}

    if "Nuclei/X Position in μm" in df.columns:
        extra_cols.append("Nuclei/X Position in μm")
        rename_map["Nuclei/X Position in μm"] = "X Position"

    if "Nuclei/Y Position in μm" in df.columns:
        extra_cols.append("Nuclei/Y Position in μm")
        rename_map["Nuclei/Y Position in μm"] = "Y Position"

    # Combine extras + biomarker columns
    final_cols = extra_cols + keep_biomarker_cols

    # Subset
    df = df[final_cols]

    # Apply renaming
    df = df.rename(columns=rename_map)

    return df