import pandas as pd
from typing import List

from config import (
    FEATURES_FILE,
    FEATURES_SHEET,
    FEATURES_START_ROW,
    FEATURES_COL_NAME,
)
from utils import clean_str


def load_features() -> List[str]:
    """Læs feature-liste fra filen og returnér en sorteret liste af unikke features."""
    if FEATURES_FILE.endswith(".csv"):
        df = pd.read_csv(FEATURES_FILE, skiprows=FEATURES_START_ROW)
    else:
        excel_obj = pd.read_excel(
            FEATURES_FILE,
            sheet_name=FEATURES_SHEET if FEATURES_SHEET is not None else None,
            skiprows=FEATURES_START_ROW,
        )

        if isinstance(excel_obj, dict):
            sheet_names = list(excel_obj.keys())
            df = excel_obj[sheet_names[0]]
        else:
            df = excel_obj

    if FEATURES_COL_NAME not in df.columns:
        raise ValueError(
            f"Kunne ikke finde kolonnen '{FEATURES_COL_NAME}' i features-filen. "
            f"Fandt kolonnerne: {list(df.columns)}"
        )

    features = sorted(
        {
            clean_str(v)
            for v in df[FEATURES_COL_NAME].dropna()
            if clean_str(v)
        }
    )

    return features
