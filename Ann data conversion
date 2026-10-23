import re
import numpy as np
import pandas as pd
import anndata as ad

def mif_csv_to_anndata(csv_path, compartment="Cells (5.0 px)", metadata=None):
    df = pd.read_csv(csv_path, low_memory=False)

    # 1. Keep only cell rows (drops the core/ROI summary rows)
    df = df[df["Annotation Group"].str.endswith("Nuclei Segmentation")].copy()
    df["core"] = df["Annotation Group"].str.extract(r"_(\d+)\.\d+\.\d+_Rectangle")[0]
    df.index = "core" + df["core"] + "_cell" + df["Annotation Index"].astype(str)

    # 2. Find the marker intensity columns -> these become X
    pat = re.compile(rf"^{re.escape(compartment)}/Mean Intensity \((.+?) - \w+\)$")
    cols = {c: pat.match(c).group(1).split("_")[0] for c in df.columns if pat.match(c)}
    cols = {c: m for c, m in cols.items() if m != "DAPI"}

    # 3. Build the AnnData object
    adata = ad.AnnData(
        X=df[list(cols)].to_numpy(np.float32),                       # cells x markers
        obs=pd.DataFrame({"core": df["core"].astype("category"),
                          "roi": df["Class group"].astype("category")},
                         index=df.index),                            # per-cell info
        var=pd.DataFrame(index=list(cols.values())),                 # marker names
    )
    adata.obsm["spatial"] = df[[f"{compartment}/X Position in μm",
                                f"{compartment}/Y Position in μm"]].to_numpy(np.float32)

    # 4. Add patient / site / treatment, given per core
    if metadata is not None:
        meta = pd.DataFrame(metadata).T
        adata.obs = adata.obs.join(meta, on="core")
        for c in meta.columns:
            adata.obs[c] = adata.obs[c].astype("category")
    return adata


adata = mif_csv_to_anndata(
    "feature_table.csv",
    metadata={
        "15": {"patient": "PatientY", "site": "tumor", "treatment": "anti-PD1"},
        "16": {"patient": "PatientY", "site": "tumor", "treatment": "anti-PD1"},
    },
)
print(adata)
adata.write_h5ad("output.h5ad")
