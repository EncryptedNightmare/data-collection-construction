# Data Collection for the Construction Industry

Dette projekt samler data relateret til byggebranchen gennem Python scripts.
Data kan fx komme fra offentlige databaser, API’er eller web scraping.

## 📦 Struktur
<pre> 
data-collection-construction/
│
├── src/
│ ├── init.py
│ ├── main.py
│ ├── scraper.py # Web scraping / API-dataindsamling
│ ├── parser.py # Databehandling og rensning
│ ├── utils.py # Hjælpefunktioner (fx logging, tidsstempler)
│ └── config.py # Indstillinger, API-nøgler, URL'er, etc.
│
├── data/
│ ├── raw/ # Ubehandlet data
│ └── processed/ # Renset og struktureret data
│
├── notebooks/
│ └── exploration.ipynb # Til analyse og tests
│
├── tests/
│ ├── test_scraper.py
│ ├── test_parser.py
│ └── test_utils.py
│
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
</pre>

## ▶️ Kør projektet
```bash
git clone https://github.com/<dit-brugernavn>/data-collection-construction.git
cd data-collection-construction
pip install -r requirements.txt
python src/main.py
```

## ⚙️ Teknologier

- Python 3.10+
- pandas – til databehandling
- groq/compound-mini

## 🧠 Formål
Projektet kan anvendes til:
- Indsamling af data fra offentlige registre, udbudsdatabaser eller byggesites
- Overvågning af trends i byggebranchen
- Dataanalyse og rapportering

## 📄 Licens
Dette projekt er udgivet under MIT License.
Du er velkommen til at bruge, ændre og dele koden frit.

---
### 🧰 **.gitignore**

