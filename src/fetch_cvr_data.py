import csv
import requests
import urllib.parse
import time

input_file = "virksomheder.csv"   # Din CSV-fil med kundelisten
output_file = "output.csv"        # Filen hvor vi gemmer resultaterne

def fetch_cvr_info(cvr_number):
    url = f"https://cvrapi.dk/api?search={cvr_number}&country=dk"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)  # <-- se alt API'et returnerer
        if "error" in data:
            return None
        return {
            "Navn": data.get("name", ""),
            "CVR": data.get("vat", ""),
            "Branche": data.get("industrydesc", ""),
            "Ansatte": data.get("employees", ""),
            "Adresse": data.get("address", ""),
            "Postnummer": data.get("zipcode", ""),
            "By": data.get("city", "")
        }
    except Exception as e:
        print(f"Fejl for CVR {cvr_number}: {e}")
        return None

def main():
    results = []

    with open(input_file, newline="", encoding="cp1252") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        next(reader)  # spring header over
        for row in reader:
            kunde = row[0].strip()
            cvr_number = row[1].strip()
            print(f"Henter data for {kunde} ({cvr_number})...")
            info = fetch_cvr_info(cvr_number)
            if info:
                results.append(info)
            else:
                results.append({
                    "Navn": kunde,
                    "CVR": cvr_number,
                    "Branche": "",
                    "Ansatte": "",
                    "Adresse": "",
                    "Postnummer": "",
                    "By": ""
                })
            time.sleep(1)  # pause for at undgå rate-limit

    # Gem resultater i ny CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Navn", "CVR", "Branche", "Ansatte", "Adresse", "Postnummer", "By"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Færdig! Resultater gemt i {output_file}")

if __name__ == "__main__":
    main()
