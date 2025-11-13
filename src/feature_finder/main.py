import csv
import time
from itertools import cycle

from config import API_KEYS, BATCH_SIZE
from features import load_features
from companies import load_companies
from analyzer import analyze_company
from client import get_client_with_key
from utils import chunked, mask_key


def main() -> None:
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

    selected_batches = batches[start_batch - 1 : stop_batch]

    print(f"\nKører batches {start_batch} → {stop_batch} af {total_batches}.\n")

    # === Kør valgte batches ===
    for batch_idx, batch in enumerate(selected_batches, start=start_batch):
        current_key = next(key_cycle)
        client = get_client_with_key(current_key)

        print(
            f"\n=== Batch {batch_idx}/{total_batches} · nøgle: {mask_key(current_key)} "
            f"· virksomheder: {len(batch)} ==="
        )

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
            fieldnames=["Company", "Website", "Feature", "Relevance", "Reason"],
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
