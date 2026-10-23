def calculate_percentages(counts, percentage_rules):
    """
    counts: dict of {sample: {phenotype: count}}
    percentage_rules: list of {"numerator": "...", "denominator": "..."}

    Returns:
        {sample: { "numerator/denominator": percentage_value }}
    """
    results = {}

    for sample, ph_counts in counts.items():
        sample_results = {}

        for rule in percentage_rules:
            num = rule["numerator"]
            den = rule["denominator"]

            num_count = ph_counts.get(num, 0)
            den_count = ph_counts.get(den, 0)

            if den_count == 0:
                pct = 0
            else:
                pct = (num_count / den_count) * 100

            label = f"{num} / {den}"
            sample_results[label] = pct

        results[sample] = sample_results

    return results