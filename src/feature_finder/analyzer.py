import os
import time
from typing import List, Dict, Tuple

from groq import Groq

from config import MODEL, MAX_OUTPUT_TOKENS, MODEL_OUTPUT_FILE
from utils import clean_str


def log_model_output(company_name: str, raw_text: str) -> None:
    """Gemmer modellens svar (rå output) i en separat logfil."""
    log_dir = os.path.dirname(MODEL_OUTPUT_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    with open(MODEL_OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Virksomhed: {company_name}\n")
        f.write(f"Tidspunkt: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 80 + "\n")
        f.write((raw_text or "").strip() + "\n")


def build_messages(company_name: str, features: List[str]) -> List[Dict[str, str]]:
    """Bygger system- og brugermeddelelser til compound-modellen."""
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
        ),
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
""".strip(),
    }

    return [system_msg, user_msg]


def parse_compound_response(
    raw: str,
    company_name: str,
    features: List[str],
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Parser svar i formatet:
      website;URL
      feature;relevance;reason

    Returnerer (website, rows) hvor rows er dicts klar til CSV.
    """
    lines = [l.strip() for l in (raw or "").splitlines() if l.strip()]
    website = ""
    rows: List[Dict[str, str]] = []

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


def analyze_company(
    client: Groq,
    company: Dict[str, str],
    features: List[str],
) -> List[Dict[str, str]]:
    """
    Kalder modellen for én virksomhed og returnerer en liste af rækker til CSV.
    Crasher ikke scriptet – ved fejl returneres en tom liste.
    """
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

            log_model_output(company["name"], raw)
            last_raw = raw

            if not raw:
                raise ValueError("Tomt svar fra modellen")

            _, rows = parse_compound_response(raw, company["name"], features)

            if rows:
                return rows

            # Hvis ingen rows, så er format forkert → kast fejl så vi kan håndtere det
            raise ValueError("Ingen gyldige feature-linjer i svaret")

        except Exception as e:
            last_error = e
            s = str(e).lower()

            # Ved rate limit → prøv igen
            if "rate limit" in s or "429" in s:
                time.sleep(1.5 * (attempt + 1))
                continue

            # Anden fejl → log og stop forsøg for denne virksomhed
            print(f"\n[DEBUG] Problem med {company['name']}: {e}")
            if last_raw:
                print("[DEBUG] Rått svar fra model:")
                print(last_raw)
            return []

    # Hvis vi ender her efter flere forsøg:
    print(f"\n[DEBUG] Kunne ikke få gyldigt svar for {company['name']} efter flere forsøg.")
    if last_raw:
        print("[DEBUG] Sidste rå svar fra model:")
        print(last_raw)
    if last_error:
        print("[DEBUG] Sidste fejl:", last_error)

    return []
