# Data Collection for the Construction Industry

Dette projekt samler data relateret til byggebranchen gennem Python scripts.
Data kan fx komme fra offentlige databaser, API’er eller web scraping.

## 📦 Struktur
<pre> ```text data-collection-construction/ │ ├── src/ │ ├── __init__.py │ ├── main.py │ ├── scraper.py # Web scraping / API-dataindsamling │ ├── parser.py # Databehandling og rensning │ ├── utils.py # Hjælpefunktioner (fx logging, tidsstempler) │ └── config.py # Indstillinger, API-nøgler, URL'er, etc. │ ├── data/ │ ├── raw/ # Ubehandlet data │ └── processed/ # Renset og struktureret data │ ├── notebooks/ │ └── exploration.ipynb # Til analyse og tests │ ├── tests/ │ ├── test_scraper.py │ ├── test_parser.py │ └── test_utils.py │ ├── requirements.txt ├── README.md ├── .gitignore └── LICENSE ``` </pre>

## ▶️ Kør projektet
```bash
git clone https://github.com/<dit-brugernavn>/data-collection-construction.git
cd data-collection-construction
pip install -r requirements.txt
python src/main.py
```

##  Krav
Se requirements.txt for afhængigheder.

## ⚙️ Teknologier

- Python 3.10+
- pandas – til databehandling
- groq/compound-mini
