import re
import pandas as pd

def clean_column_names(df, biomarkers, filename):
    """
    Clean and standardize Horizon export column names using the biomarker list
    from the orientation file. Produces names like:
        'Nuclei FOXP3 Mean Intensity'
        'Cell CD14 Threshold'
        'Cytoplasm CD141 Mean Intensity'
    """

    df = df.copy()


    # Fix encoding 
    df.columns = (
        df.columns
        .str.replace("Î¼", "μ", regex=False)
        .str.replace("Îœ", "μ", regex=False)
        .str.replace("Â²", "²", regex=False)
    )


    # Detect duplicate raw column names
    duplicates = df.columns[df.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(
            f"Duplicate column names detected in input file '{filename}': {duplicates}"
        )


    #  Prepare biomarker list for exact matching
    biomarkers_clean = [b.strip() for b in biomarkers]

    # Horizon column parser
    def parse_horizon_column(col):
        """
        Parse Horizon-style biomarker columns such as:
            'Nuclei/Mean Intensity (FOXP3 TBL clone - Cy5)'
            'Cells (distance 5 px)/Mean Intensity (CD14_CST_100 - TRITC)'
            'Nuclei/Mean Intensity (FOXP3 ...)/Threshold (440)'
        """
        # Normalize hidden characters
        col_norm = (
            col.replace("\ufeff", "")
            .replace("\u200b", "")
            .replace("\xa0", " ")
            .strip()
        )
        col = re.sub(r"\(distance\s+\d+(\.\d+)?\s+px\)/", "", col)


        # Compartment extraction
        comp_match = re.match(r"^(Nuclei|Cell|Cells|Cytoplasm)", col_norm, flags=re.IGNORECASE)
        if not comp_match:
            return None

        raw_comp = comp_match.group(1).lower()

        if raw_comp.startswith("nuclei"):
            compartment = "Nuclei"
        elif raw_comp.startswith("cell"):
            compartment = "Cell"
        elif raw_comp.startswith("cytoplasm"):
            compartment = "Cytoplasm"
        else:
            return None


        # Measurement extraction
        if "Threshold" in col:
            measurement = "Threshold"
        elif "Mean Intensity" in col:
            measurement = "Mean Intensity"
        else:
            return None



        # Biomarker extraction
        paren = re.search(r"\((.*?)\)", col)
        if not paren:
            return None

        inside = paren.group(1)

        # Match biomarker using flexible prefix logic, but preserve original spelling
        biomarker_found = None
        for b in biomarkers_clean:
            # Match b at a word boundary, followed by end, underscore, hyphen, or space
            pattern = rf"\b{re.escape(b)}(?=$|[_\-\s])"
            if re.search(pattern, inside, flags=re.IGNORECASE):
                biomarker_found = b   # <-- THIS preserves original capitalization
                break

        if biomarker_found is None:
            return None

        # Build final cleaned name
        return f"{compartment} {biomarker_found} {measurement}"


    # 5. Apply renaming logic
    new_columns = {}

    for col in df.columns:
        parsed = parse_horizon_column(col)
        new_columns[col] = parsed if parsed else col

    df.rename(columns=new_columns, inplace=True)


    # 6. Detect duplicates after cleaning
    duplicates_after = df.columns[df.columns.duplicated()].tolist()
    if duplicates_after:
        raise ValueError(
            f"Duplicate column names created during cleaning in file '{filename}': {duplicates_after}"
        )

    return df