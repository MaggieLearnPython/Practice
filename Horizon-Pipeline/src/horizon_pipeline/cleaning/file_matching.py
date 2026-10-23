import pandas as pd
from pathlib import Path

def match_sample_name(file_stem, sample_names):
    file_stem = file_stem.lower()
    matches = [s for s in sample_names if s.lower() in file_stem]

    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches[0]

    return max(matches, key=len)