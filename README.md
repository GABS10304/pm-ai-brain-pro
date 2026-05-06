# 🧠 PM & Sales AI Brain Pro (Local Suite)
Ein 100% lokales, datenschutzkonformes (Offline) KI-Ökosystem für Product Manager und RevOps zur automatisierten Auswertung von qualitativem Feedback sowie quantitativen Sales-Daten.

## 🏗️ Workflow-Architektur & Skripte
Das System besteht aus mehreren isolierten Pipelines, die komplett lokal laufen:

### 1. Daten-Aufbereitung (Hintergrund-Skripte)
* **Der CSV-Extraktor (`rag.py`):** Filtert NPS- und Umfragedaten und extrahiert harte Problem-Fakten.
* **Der HTML-Schredder (`html_schredder.py`):** Säubert rohe HTML-Support-Tickets von Code & E-Mail-Verläufen und extrahiert den Software-Pain-Point. (*Nutzt das schnelle Modell `llama3.2`*).

### 2. Das Streamlit Multipage-Portal (Frontend)
Eine interaktive Web-UI mit zwei dedizierten, fachspezifischen Tools:

* **Das PM Copilot Brain (`pm_copilot.py`):** 
  Interaktive Chat-GUI für das Product Management. Fasst aggregierte Daten (aus Schredder und CSV) zusammen, clustert sie und beantwortet Dialog-Fragen fokussiert im *Problem Space*. (*Nutzt `qwen3.5:9b`*).
* **Das Sales Strategy Brain (`pages/2_Sales_Strategy_Brain.py`):** 
  Ein deterministisches RevOps-Tool. Python berechnet harte quantitative KPIs (Netto-Werte, Rabattdisziplin, Contract-Keys) zu 100% halluzinationsfrei. Die KI generiert im Anschluss basierend auf den aggregierten Tabellen strategische ICP-Kandidaten und ein textbasiertes Sales Cheat Sheet.

## 💻 Installation (Lokal)
Voraussetzung: [Ollama](https://ollama.com/) muss installiert sein.

1. Modelle lokal herunterladen:
   `ollama pull llama3.2`
   `ollama pull qwen3.5:9b`
2. Python Abhängigkeiten installieren:
   `pip install -r requirements.txt`
3. Die App starten:
   `streamlit run pm_copilot.py`

*Hinweis: Beispieldaten, CSV-Dateien und Vertragsdaten sind aus Datenschutzgründen via .gitignore vom Repository ausgeschlossen.*