import pandas as pd
from typing import List, Dict

from config import COMPANIES_FILE, COMPANY_SHEET_CONFIG
from utils import clean_str


def load_companies() -> List[Dict[str, str]]:
    """
    Læs virksomhedsnavne fra de konfigurerede ark i COMPANIES_FILE.
    Returnerer en liste af dicts: {"name": ..., "sheet": ...}
    """
    xls = pd.ExcelFile(COMPANIES_FILE)
    companies: List[Dict[str, str]] = []
    seen = set()

    for sheet_name, cfg in COMPANY_SHEET_CONFIG.items():
        if sheet_name not in xls.sheet_names:
            print(f"Advarsel: ark '{sheet_name}' findes ikke i {COMPANIES_FILE}, springer over.")
            continue

        start_row = cfg.get("start_row", 0)

        df = pd.read_excel(
            xls,
            sheet_name=sheet_name,
            usecols="D",      # kolonne D
            header=None,      # ingen header
            skiprows=start_row,
        )

        for _, row in df.iterrows():
            name = clean_str(row.iloc[0])
            if not name:
                continue

            key = (name, sheet_name)
            if key in seen:
                continue
            seen.add(key)

            companies.append({
                "name": name,
                "sheet": sheet_name,
            })

    return companies
