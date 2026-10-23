def calculate_densities(counts_dict, area_dict):
    """
    counts_dict: { sample_name: { phenotype: count } }
    area_dict:   { sample_name: area_in_square_microns }

    Returns:
        { sample_name: { phenotype: density_per_mm2 } }
    """
    results = {}

    for sample, pheno_counts in counts_dict.items():
        area_um2 = area_dict.get(sample)

        if area_um2 is None or area_um2 == 0:
            results[sample] = {ph: None for ph in pheno_counts}
            continue

        # Convert µm² → mm²
        area_mm2 = area_um2 / 1_000_000

        results[sample] = {
            ph: count / area_mm2
            for ph, count in pheno_counts.items()
        }

    return results