import os
import pandas as pd
from groq import Groq
import csv
import time
from itertools import cycle
import sys
from datetime import datetime


MODEL_OUTPUT_FILE = f"model_outputs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

def log_model_output(company_name: str, raw_text: str):
    """Gemmer modellens svar (rå output) i en separat fil."""
    with open(MODEL_OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Virksomhed: {company_name}\n")
        f.write(f"Tidspunkt: {datetime.now()}\n")
        f.write("-"*80 + "\n")
        f.write(raw_text.strip() + "\n")


# ========== KONFIGURATION ==========

# 1) Features-fil
FEATURES_FILE = "features.xlsx"      # eller .csv
FEATURES_SHEET = "Features"          # hvis CSV -> brug None
FEATURES_START_ROW = 0               # 0-baseret (0 = første række er header)
FEATURES_COL_NAME = "Features"       # præcis kolonnenavnet i arket

# 2) Virksomheder-fil (med flere ark, uden URLs)
COMPANIES_FILE = "Branche_og_lead_kartotek.xlsx"

# Ark-navne vi vil læse + hvilken række (0-baseret) vi starter fra i hver
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

MODEL = "groq/compound-mini"
MAX_OUTPUT_TOKENS = 400


# ========== KLIENT ==========


API_KEYS = [
    "",
    # tilføj flere hvis du har
]
BATCH_SIZE = 8  # kør 8 virksomheder ad gangen

def get_client_with_key(api_key: str) -> Groq:
    if not api_key:
        raise RuntimeError("API key mangler!")
    return Groq(
        api_key=api_key,
        default_headers={"Groq-Model-Version": "latest"},
    )

def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def mask_key(k: str) -> str:
    if not k:
        return "<empty>"
    return k[:6] + "..." + k[-4:]



def clean_str(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


# ========== FEATURES ==========

def load_features():
    if FEATURES_FILE.endswith(".csv"):
        df = pd.read_csv(FEATURES_FILE, skiprows=FEATURES_START_ROW)
    else:
        excel_obj = pd.read_excel(
            FEATURES_FILE,
            sheet_name=FEATURES_SHEET if FEATURES_SHEET is not None else None,
            skiprows=FEATURES_START_ROW
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


# ========== VIRKSOMHEDER ==========

def load_companies():
    xls = pd.ExcelFile(COMPANIES_FILE)
    companies = []
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
            skiprows=start_row
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


# ========== PROMPT & ANALYSE UDEN JSON ==========

def build_messages(company_name: str, features: list[str]):
    features_str = "\n".join(f"- {f}" for f in features)

    system_msg = {
        "role": "system",
        "content": (
            "Du er en B2B-markedsanalytiker med adgang til web-søgning og website-besøg "
            "via groq/compound værktøjer. "
            "For hver virksomhed skal du:\n"
            "1) Find den mest sandsynlige officielle hjemmeside.\n"
            "2) Besøg siden og forstå hvad de tilbyder.\n"
            "3) For hver feature: vurder relevans.\n"
            "4) Svar KUN i følgende format (meget vigtigt):\n"
            "   Første linje: website;URL\n"
            "   Derefter én linje pr. feature:\n"
            "   feature_navn;relevance;reason\n"
            "   hvor relevance er en af: high, medium, low, unknown.\n"
            "Ingen ekstra tekst, ingen forklaring udenfor dette format."
        )
    }

    user_msg = {
        "role": "user",
        "content": f"""
Virksomhed: "{company_name}"

Features:
{features_str}

Format KRAV (ingen ekstra tekst):

website;https://virksomhedens-website.her
feature_navn;high|medium|low|unknown;kort forklaring på dansk
feature_navn;high|medium|low|unknown;kort forklaring på dansk
...
""".strip()
    }

    return [system_msg, user_msg]


def parse_compound_response(raw: str, company_name: str, features: list[str]):
    """
    Parser svar i formatet:
      website;URL
      feature;relevance;reason

    Returnerer (website, [rows]) hvor rows er dicts klar til CSV.
    """
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    website = ""
    rows = []

    # Lav et opslag så vi kan matche case-insensitivt på features
    feature_map = {f.lower(): f for f in features}

    for i, line in enumerate(lines):
        parts = [p.strip() for p in line.split(";", 2)]

        # Første linje: website;URL (case-insensitiv)
        if i == 0 and len(parts) >= 2 and parts[0].lower() == "website":
            website = parts[1]
            continue

        if len(parts) < 3:
            continue

        raw_feature, raw_relevance, reason = parts[0], parts[1].lower(), parts[2]

        # Match feature case-insensitivt
        feature_key = raw_feature.lower()
        if feature_key not in feature_map:
            continue
        feature = feature_map[feature_key]

        if raw_relevance not in ["high", "medium", "low", "unknown"]:
            continue

        rows.append({
            "Company": company_name,
            "Website": website,
            "Feature": feature,
            "Relevance": raw_relevance,
            "Reason": reason,
        })

    return website, rows



def analyze_company(client: Groq, company: dict, features: list[str]):
    messages = build_messages(company["name"], features)

    last_raw = None
    last_error = None

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=MAX_OUTPUT_TOKENS,
            )

            msg = completion.choices[0].message
            content = msg.content

            if isinstance(content, list):
                raw = "".join(
                    str(c.get("text", "")) if isinstance(c, dict) else str(c)
                    for c in content
                ).strip()
            else:
                raw = (content or "").strip()
                # Gem det rå model-output
            
            log_model_output(company["name"], raw)

            last_raw = raw

            if not raw:
                raise ValueError("Tomt svar fra modellen")

            website, rows = parse_compound_response(raw, company["name"], features)

            if rows:
                return rows

            # Hvis ingen rows, så er format forkert → kast fejl så vi kan logge / evt. retry
            raise ValueError("Ingen gyldige feature-linjer i svaret")

        except Exception as e:
            last_error = e
            s = str(e).lower()

            # Ved rate limit → prøv igen
            if "rate limit" in s or "429" in s:
                time.sleep(1.5 * (attempt + 1))
                continue

            # Anden fejl → log og stop forsøg
            print(f"\n[DEBUG] Problem med {company['name']}: {e}")
            if last_raw:
                print("[DEBUG] Rått svar fra model:")
                print(last_raw)
            # Returner tom liste så scriptet fortsætter med næste virksomhed
            return []

    # Hvis vi ender her efter kun rate limit eller gentagne fejl:
    print(f"\n[DEBUG] Kunne ikke få gyldigt svar for {company['name']} efter flere forsøg.")
    if last_raw:
        print("[DEBUG] Sidste rå svar fra model:")
        print(last_raw)
    if last_error:
        print("[DEBUG] Sidste fejl:", last_error)

    return []  # vigtigst: ikke crashe, bare ingen data for den virksomhed



# ========== MAIN ==========

#def main(): # gammel main
    #client = get_client()
    features = load_features()
    companies = load_companies()

    csv_rows = []

    for c in companies:
        print(f"Analyserer: {c['name']} (ark: {c['sheet']})")
        try:
            rows = analyze_company(client, c, features)
            csv_rows.extend(rows)
        except Exception as e:
            print(f"Fejl ved {c['name']}: {e}")

    # Skriv direkte til CSV
    csv_file = "results_compound.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Company", "Website", "Feature", "Relevance", "Reason"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nCSV-fil gemt som: {csv_file}")

    # Kort overblik i terminalen
    print("\n=== OVERBLIK ===")
    by_company = {}
    for row in csv_rows:
        by_company.setdefault((row["Company"], row["Website"]), []).append(row)

    for (company, website), rows in by_company.items():
        print(f"\n{company} - {website}")
        for r in rows:
            print(f"  - {r['Feature']}: {r['Relevance']} ({r['Reason']})")

def main():
    features = load_features()
    companies = load_companies()

    csv_rows = []

    key_cycle = cycle(API_KEYS)
    batches = list(chunked(companies, BATCH_SIZE))
    total_batches = len(batches)

    print(f"\nDer er i alt {total_batches} batches á {BATCH_SIZE} virksomheder.")

    # === Brugeren vælger startbatch ===
    while True:
        try:
            start_batch = int(input(f"Hvilket batch vil du starte fra? (1–{total_batches}): "))
            if 1 <= start_batch <= total_batches:
                break
            else:
                print("Ugyldigt batchnummer – prøv igen.")
        except ValueError:
            print("Skriv et helt tal, fx 1 eller 2.")

    # === Brugeren vælger stoppunkt ===
    while True:
        try:
            stop_batch = int(input(f"Hvilket batch vil du stoppe ved? (kan maks. være {total_batches}): "))
            if start_batch <= stop_batch <= total_batches:
                break
            else:
                print(f"Ugyldigt batchnummer – skal være mellem {start_batch} og {total_batches}.")
        except ValueError:
            print("Skriv et helt tal, fx 5 eller 10.")

    # Slice batch-listen til det valgte interval
    batches = batches[start_batch - 1:stop_batch]

    print(f"\nKører batches {start_batch} → {stop_batch} af {total_batches}.\n")

    # === Kør valgte batches ===
    for batch_idx, batch in enumerate(batches, start=start_batch):
        current_key = next(key_cycle)
        client = get_client_with_key(current_key)

        print(f"\n=== Batch {batch_idx}/{total_batches} · nøgle: {mask_key(current_key)} · virksomheder: {len(batch)} ===")

        for c in batch:
            print(f"Analyserer: {c['name']} (ark: {c['sheet']})")
            try:
                rows = analyze_company(client, c, features)
                csv_rows.extend(rows)
            except Exception as e:
                print(f"Fejl ved {c['name']}: {e}")

        # Valgfri pause mellem batches for at undgå rate limit
        time.sleep(0.5)

    # === Gem resultater ===
    csv_file = f"results_compound_batch_{start_batch}_to_{stop_batch}.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Company", "Website", "Feature", "Relevance", "Reason"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nCSV-fil gemt som: {csv_file}")

    # === Kort overblik ===
    print("\n=== OVERBLIK ===")
    by_company = {}
    for row in csv_rows:
        by_company.setdefault((row["Company"], row["Website"]), []).append(row)

    for (company, website), rows in by_company.items():
        print(f"\n{company} - {website}")
        for r in rows:
            print(f"  - {r['Feature']}: {r['Relevance']} ({r['Reason']})")

    print(f"\n✅ Færdig med batches {start_batch} → {stop_batch}.")


if __name__ == "__main__":
    main()
