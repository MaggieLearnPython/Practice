import pandas as pd

def load_orientation_file(path):

    # Read biomarker sheet 

    df = pd.read_excel(path, sheet_name=0)

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Clean biomarker names 
    df["biomarkers"] = df["biomarkers"].astype(str).str.strip()

    # Normalize compartment names 
    df["compartment"] = (
        df["compartment"].astype(str).str.strip().str.title()
    )

    # Read phenotype list sheet
    try:
        phenotype_df = pd.read_excel(path, sheet_name="phenotypes")
        phenotype_df = phenotype_df.dropna()
        df.phenotypes = phenotype_df.iloc[:, 0].astype(str).str.strip().tolist()
    except Exception:
        df.phenotypes = []


    # Read percentage rules sheet

    try:
        percent_df = pd.read_excel(path, sheet_name="percentages")
        percent_df = percent_df.dropna(subset=["Numerator", "Denominator"])

        df.percentage_rules = [
            {
                "numerator": num.strip(),
                "denominator": den.strip()
            }
            for num, den in zip(percent_df["Numerator"], percent_df["Denominator"])
        ]
    except Exception:
        df.percentage_rules = []

    return df
