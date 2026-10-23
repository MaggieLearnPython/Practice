import pandas as pd
from pathlib import Path

def calculate_sample_area(df):
    """
    Calculate sample area using annotation rows.
    ROI areas are added, Exclusion areas are subtracted, Main is ignored.
    """

    area_col = "Area in μm²"
    class_col = "Class group"

    # 1. Keep only annotation rows (area column has a value)
    ann = df[df[area_col].notna()].copy()

    if ann.empty:
        return 0  # No annotations found

    # 2. Normalize class group text
    ann[class_col] = ann[class_col].astype(str).str.lower().str.strip()

    # 3. Identify ROI and Exclusion rows
    roi_rows = ann[ann[class_col].str.startswith("roi")]
    exclusion_rows = ann[ann[class_col].str.startswith("exclusion")]

    # 4. Compute sums
    roi_area = roi_rows[area_col].sum()
    exclusion_area = exclusion_rows[area_col].sum()

    # 5. Final area
    final_area = roi_area - exclusion_area

    return final_area
