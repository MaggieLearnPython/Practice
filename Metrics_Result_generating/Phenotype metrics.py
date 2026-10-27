"""
Phenotype counts and densities, per ROI and per sample.

Only input: the folder with the pipeline's cleaned CSVs (one per sample, e.g.
TBL-066-S0024.csv). Each needs the columns "Class group", "sample_name",
"sample_area", "roi_area" and "<Compartment> <Marker> Threshold".

The population list is taken from that same folder: any .xlsx file with
"population" in its name. If there is none, POPULATION_LIST below is used.
Any layout works: every non-empty cell below the header row of each column is
a phenotype, and the header is its category (e.g. "CD3+Populations").

Output: phenotype_metrics.xlsx, saved in the cleaned folder, with sheets
  Sample counts, Sample density, ROI counts, ROI density (each sample's ROIs
  followed by Mean and SD rows), Areas, Long format, and Phenotypes (how each
  population was read).

Density is cells per mm². ROI areas (exclusions subtracted, container ROIs
left out) are calculated by the pipeline and stored in the "roi_area" column.
SD is the sample standard deviation across a sample's ROIs (n - 1).

Usage: set CLEANED_FOLDER below and press Run, or
  python phenotype_metrics.py "path\\to\\cleaned folder"
"""

import argparse
import difflib
import re
from pathlib import Path

import pandas as pd

# ---- EDIT THIS (keep the r and the quotes) -----------------------------------
CLEANED_FOLDER = r"D:\Maggie\Barbie STING October 2026\S0024_Data for Comp Bio\Results"

# Used only if no population list (.xlsx with "population" in its name) is found
# in CLEANED_FOLDER.
POPULATION_LIST = r"D:\Maggie\Barbie STING October 2026\S0024_Data for Comp Bio\Results\Barbie STING COMET population List.xlsx"
OUTPUT_NAME = "phenotype_metrics.xlsx"
# -----------------------------------------------------------------------------
# Marker names in the population list must match the marker names in the
# result sheets. Matching ignores only upper/lower case and hyphens/underscores/
# spaces (PD1 = PD-1). Anything else that does not match stops the script with
# a list of every unmatched marker, before any output is written.

THRESHOLD_COL = re.compile(r"^(Nuclei|Cell|Cytoplasm)\s+(.+?)\s+Threshold$")
UM2_PER_MM2 = 1_000_000


def norm(name):
    """Comparison key for marker names: case-, hyphen-, space- and underscore-insensitive."""
    return re.sub(r"[\s_\-]", "", str(name)).upper()


# ---------------------------------------------------------------- inputs
def read_population_list(path):
    """Return a list of (category, phenotype) in the order they appear."""
    sheet = pd.read_excel(path, sheet_name=0, header=None, dtype=str)
    pops, seen = [], set()
    for col in sheet.columns:
        category = str(sheet.iloc[0, col]).strip() if pd.notna(sheet.iloc[0, col]) else f"Column {col + 1}"
        for value in sheet.iloc[1:, col].dropna():
            phenotype = re.sub(r"\s+", "", str(value))
            if phenotype and phenotype not in seen:
                seen.add(phenotype)
                pops.append((category, phenotype))
    if not pops:
        raise SystemExit(f"No populations found in {path}")
    return pops


def read_csv(path):
    try:
        df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin1", low_memory=False)
    df.columns = (df.columns.str.replace("\ufeff", "", regex=False).str.strip()
                  .str.replace("Î¼", "μ", regex=False).str.replace("Â²", "²", regex=False))
    return df


def threshold_columns(df):
    """{normalized marker name: (display name, column)} for every threshold column."""
    out = {}
    for col in df.columns:
        m = THRESHOLD_COL.match(col)
        if m:
            out[norm(m.group(2))] = (m.group(2), col)
    return out


def as_bool(series):
    if series.dtype == bool:
        return series
    text = series.astype(str).str.strip().str.lower()
    return text.isin(["true", "1", "1.0", "yes", "positive", "pos"])


# ---------------------------------------------------------------- phenotypes
def parse_phenotype(rule, marker_keys):
    """
    'CD3+CD8+PD1-' -> [('CD3', True), ('CD8', True), ('PD1', False)]
    Markers are matched against known names (longest first), so names that
    contain hyphens (PD-L1) work. Returns (parsed, error).
    """
    if norm(rule) in ("TOTALCELLS", "ALLCELLS"):
        return [], None
    candidates = sorted(marker_keys, key=len, reverse=True)
    parsed, i = [], 0
    while i < len(rule):
        for name in candidates:
            if rule[i:i + len(name)].upper() == name.upper() and i + len(name) < len(rule) \
                    and rule[i + len(name)] in "+-":
                parsed.append((name, rule[i + len(name)] == "+"))
                i += len(name) + 1
                break
        else:
            # Unknown marker: take the text up to the next + or - so it can be reported.
            m = re.match(r"([^+\-]+)([+\-])", rule[i:])
            if not m:
                return None, f"cannot read '{rule[i:]}'"
            parsed.append((m.group(1), m.group(2) == "+"))
            i += len(m.group(0))
    return parsed, None


def build_masks(df, pops):
    """Boolean mask per phenotype, plus a status table describing each one."""
    cols = threshold_columns(df)
    # Spellings accepted for each marker present in the data
    lookup = {}
    for key, (display, col) in cols.items():
        lookup[display] = col
        lookup[key] = col
    known_names = set(lookup)

    masks, status = {}, []
    for category, rule in pops:
        parsed, err = parse_phenotype(rule, known_names)
        if err:
            status.append((category, rule, "", f"NOT COMPUTED: {err}"))
            continue
        missing = [m for m, _ in parsed if m not in lookup and norm(m) not in cols]
        if missing:
            status.append((category, rule, "", f"NOT COMPUTED: marker(s) not in data: {', '.join(missing)}"))
            continue
        mask = pd.Series(True, index=df.index)
        used = []
        for marker, positive in parsed:
            col = lookup.get(marker) or cols[norm(marker)][1]
            pos = as_bool(df[col])
            mask &= pos if positive else ~pos
            used.append(f"{col} = {positive}")
        masks[rule] = mask
        status.append((category, rule, " AND ".join(used) or "all cells", "OK"))
    return masks, status


def check_markers(files, pops):
    """
    Before computing anything, check every marker in the population list against
    every result sheet. Stops with one error listing ALL unmatched markers.
    """
    unmatched = {}      # marker -> {"populations": set, "samples": set}
    unreadable = []     # (population, reason)
    loose = {}          # population spelling -> data spelling (e.g. PD1 -> PD-1)
    data_markers = set()

    for f in files:
        df = read_csv(f)
        cols = threshold_columns(df)
        if not cols:
            continue
        sample = str(df["sample_name"].iloc[0]) if "sample_name" in df.columns else f.stem
        data_markers |= {display for display, _ in cols.values()}
        known = {display for display, _ in cols.values()} | set(cols)
        for _, rule in pops:
            parsed, err = parse_phenotype(rule, known)
            if err:
                unreadable.append((rule, err))
                continue
            for marker, _ in parsed:
                if norm(marker) in cols:
                    display = cols[norm(marker)][0]
                    if marker != display:
                        loose[marker] = display
                else:
                    entry = unmatched.setdefault(marker, {"populations": set(), "samples": set()})
                    entry["populations"].add(rule)
                    entry["samples"].add(sample)

    for spelled, display in sorted(loose.items()):
        print(f"  Note: '{spelled}' in the population list matched '{display}' in the data")

    if not unmatched and not unreadable:
        return

    lines = ["", "=" * 70,
             "STOPPED: the population list does not match the result sheets.",
             "Nothing was written. Fix the names below and run again.", "=" * 70]
    if unmatched:
        lines.append(f"\n{len(unmatched)} marker(s) not found in the data:\n")
        for marker in sorted(unmatched):
            info = unmatched[marker]
            keys = {norm(m): m for m in data_markers}
            close = [keys[k] for k in difflib.get_close_matches(norm(marker), list(keys), n=2, cutoff=0.6)]
            hint = f"   did you mean: {', '.join(close)}?" if close else ""
            lines.append(f"  - {marker}{hint}")
            lines.append(f"      used in: {', '.join(sorted(info['populations']))}")
            lines.append(f"      missing in: {', '.join(sorted(info['samples']))}")
    if unreadable:
        lines.append("\nPopulations that could not be read:")
        for rule, err in sorted(set(unreadable)):
            lines.append(f"  - {rule}: {err}")
    lines.append(f"\nMarkers available in the data:\n  {', '.join(sorted(data_markers))}")
    lines.append("\nEither rename the marker in the population list to match the data, or, if the")
    lines.append("marker is missing from the data, check the biomarker names in the orientation")
    lines.append("file and rerun the pipeline.")
    raise SystemExit("\n".join(lines))


# ---------------------------------------------------------------- inputs (folder)
def find_population_list(folder):
    found = sorted(f for f in Path(folder).glob("*.xlsx")
                   if "population" in f.name.lower() and not f.name.startswith("~$"))
    if len(found) > 1:
        raise SystemExit("More than one population list in the folder; keep only one:\n  "
                         + "\n  ".join(f.name for f in found))
    if found:
        return found[0]
    if POPULATION_LIST and Path(POPULATION_LIST).is_file():
        return Path(POPULATION_LIST)
    raise SystemExit(f"No population list found. Put an .xlsx with 'population' in its name in\n"
                     f"  {folder}\nor set POPULATION_LIST at the top of this script.")


def add_mean_sd(table):
    """table: rows = (Sample, ROI). Adds Mean and SD rows after each sample's ROIs."""
    table = table.reset_index()
    pheno_cols = [c for c in table.columns if c not in ("Sample", "ROI")]
    blocks = []
    for sample, block in table.groupby("Sample", sort=False):
        values = block[pheno_cols].apply(pd.to_numeric, errors="coerce")
        mean = values.mean()
        sd = values.std(ddof=1)  # sample SD; empty if the sample has only one ROI
        blocks += [block,
                   pd.DataFrame([{"Sample": sample, "ROI": "Mean", **mean.to_dict()},
                                 {"Sample": sample, "ROI": "SD", **sd.to_dict()}])]
    return pd.concat(blocks, ignore_index=True)


# ---------------------------------------------------------------- main
def run(cleaned_folder):
    cleaned_folder = Path(cleaned_folder)
    if not cleaned_folder.is_dir():
        raise SystemExit(f"Folder does not exist: {cleaned_folder}")
    population_list = find_population_list(cleaned_folder)
    output_file = cleaned_folder / OUTPUT_NAME

    pops = read_population_list(population_list)
    print(f"Read {len(pops)} populations from {population_list.name}")
    pops = [("All cells", "Total Cells")] + [p for p in pops if norm(p[1]) != "TOTALCELLS"]
    order = [rule for _, rule in pops]
    category = {rule: cat for cat, rule in pops}

    files = []
    for f in sorted(cleaned_folder.glob("*.csv")):
        header = read_csv_header(f)
        if "Class group" in header and any(THRESHOLD_COL.match(c) for c in header):
            files.append(f)
        else:
            print(f"Ignoring {f.name}: not a cleaned sample file")
    if not files:
        raise SystemExit(f"No cleaned sample CSVs in {cleaned_folder}")

    print("Checking marker names...")
    check_markers(files, pops)
    print("All markers matched.")

    roi_rows, sample_rows, area_rows, status_rows = [], [], [], []
    for f in files:
        df = read_csv(f)
        sample = str(df["sample_name"].iloc[0]) if "sample_name" in df.columns else f.stem
        print(f"\n{sample}: {len(df):,} cells")
        df["Class group"] = df["Class group"].astype(str).str.strip()
        rois = sorted(df["Class group"].unique())

        masks, status = build_masks(df, pops)
        status_rows += [(sample, *s) for s in status]

        # Areas (µm²) from the cleaned sheet
        if "roi_area" in df.columns:
            roi_area = {r: a for r, a in df.groupby("Class group")["roi_area"].first().items() if pd.notna(a) and a > 0}
            for r in rois:
                if r not in roi_area:
                    print(f"  WARNING: no area for {r}; its density is left empty")
        else:
            roi_area = {}
            print("  WARNING: no 'roi_area' column (cleaned with the old pipeline); ROI densities left empty")
        sample_area = float(df["sample_area"].iloc[0]) if "sample_area" in df.columns else None
        if not sample_area:
            print("  WARNING: no sample area; sample densities left empty")
            sample_area = None

        for r in rois:
            a = roi_area.get(r)
            area_rows.append({"Sample": sample, "ROI": r, "Area (µm²)": a,
                              "Area (mm²)": a / UM2_PER_MM2 if a else None,
                              "Cells": int((df["Class group"] == r).sum())})
        area_rows.append({"Sample": sample, "ROI": "All ROIs", "Area (µm²)": sample_area,
                          "Area (mm²)": sample_area / UM2_PER_MM2 if sample_area else None,
                          "Cells": len(df)})

        # Counts and densities
        in_roi = {r: df["Class group"] == r for r in rois}
        for rule in order:
            m = masks[rule]
            for r in rois:
                n = int((m & in_roi[r]).sum())
                a = roi_area.get(r)
                roi_rows.append({"Sample": sample, "ROI": r, "Category": category[rule],
                                 "Phenotype": rule, "Count": n,
                                 "Area (mm²)": a / UM2_PER_MM2 if a else None,
                                 "Density (cells/mm²)": n / (a / UM2_PER_MM2) if a else None})
            n = int(m.sum())
            sample_rows.append({"Sample": sample, "ROI": "All ROIs", "Category": category[rule],
                                "Phenotype": rule, "Count": n,
                                "Area (mm²)": sample_area / UM2_PER_MM2 if sample_area else None,
                                "Density (cells/mm²)": n / (sample_area / UM2_PER_MM2) if sample_area else None})

    long = pd.DataFrame(sample_rows + roi_rows)

    def wide(rows, value, index):
        t = pd.DataFrame(rows).pivot_table(index=index, columns="Phenotype", values=value,
                                           aggfunc="first", dropna=False, sort=False)
        return t.reindex(columns=order)

    with pd.ExcelWriter(output_file) as w:
        wide(sample_rows, "Count", "Sample").to_excel(w, sheet_name="Sample counts")
        wide(sample_rows, "Density (cells/mm²)", "Sample").to_excel(w, sheet_name="Sample density")
        add_mean_sd(wide(roi_rows, "Count", ["Sample", "ROI"])).to_excel(w, sheet_name="ROI counts", index=False)
        add_mean_sd(wide(roi_rows, "Density (cells/mm²)", ["Sample", "ROI"])).to_excel(w, sheet_name="ROI density", index=False)
        pd.DataFrame(area_rows).to_excel(w, sheet_name="Areas", index=False)
        long.to_excel(w, sheet_name="Long format", index=False)
        pd.DataFrame(status_rows, columns=["Sample", "Category", "Phenotype", "Definition used", "Status"]) \
            .to_excel(w, sheet_name="Phenotypes", index=False)

    print(f"\nSaved: {output_file}")


def read_csv_header(path):
    try:
        cols = pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns
    except UnicodeDecodeError:
        cols = pd.read_csv(path, nrows=0, encoding="latin1").columns
    return [c.replace("﻿", "").strip() for c in cols]


def main():
    p = argparse.ArgumentParser(description="Phenotype counts and densities per ROI and per sample.")
    p.add_argument("cleaned_folder", nargs="?", default=CLEANED_FOLDER,
                   help="folder with the cleaned CSVs (default: CLEANED_FOLDER in the script)")
    run(p.parse_args().cleaned_folder)


if __name__ == "__main__":
    main()