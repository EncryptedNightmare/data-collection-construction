from datetime import datetime

# ========== LOGGING ==========

MODEL_OUTPUT_FILE = f"logs/model_outputs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

# ========== FEATURES-FIL ==========

FEATURES_FILE = "data/raw/features.xlsx"      # eller "data/raw/features.xlsx"
FEATURES_SHEET = "Features"          # hvis CSV -> sæt til None
FEATURES_START_ROW = 0               # 0-baseret (0 = første række er header)
FEATURES_COL_NAME = "Features"       # præcis kolonnenavnet i arket

# ========== VIRKSOMHEDS-FIL ==========

COMPANIES_FILE = "data/raw/Branche_og_lead_kartotek.xlsx"

COMPANY_SHEET_CONFIG = {
    "410000": {"start_row": 1},
    "421100": {"start_row": 1},
    "422100": {"start_row": 1},
    "429900": {"start_row": 1},
    "431100": {"start_row": 1},
    "431200": {"start_row": 1},
    "432200": {"start_row": 1},
    "433200": {"start_row": 1},
    "433300": {"start_row": 1},
    "434200": {"start_row": 1},
    "435000": {"start_row": 1},
    "439100": {"start_row": 1},
    "439900": {"start_row": 1},
    "681200": {"start_row": 1},
    "711210": {"start_row": 1},
    "711240": {"start_row": 1},
    "711290": {"start_row": 1},
    "813000": {"start_row": 1},
}

# ========== MODEL ==========

MODEL = "groq/compound-mini"
MAX_OUTPUT_TOKENS = 400

# ========== API-KEYS & BATCHES ==========

API_KEYS = [
    "",        # <- indsæt dine nøgler her
    # "groq_key_2",
    # "groq_key_3",
]

BATCH_SIZE = 8  # antal virksomheder pr. batch

