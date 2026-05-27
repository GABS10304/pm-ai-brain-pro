import os
import pandas as pd
from google.cloud import bigquery

# ==========================================
# 1. SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "gcp-key.json")

# HIER NEHMEN WIR DEINE UMFRAGEN CSV
INPUT_CSV = os.path.join(BASE_DIR, "Schnelles_PM_Backlog.csv")

# 🚨 HIER IST DER NAME, DEN DEIN DASHBOARD SUCHT
BIGQUERY_TABLE = "pm-analytics-496606.pm_daten.anonymes_pm_backlog"

def upload():
    print(f"🚀 Starte Cloud-Upload...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"⚠️ Datei nicht gefunden!")
        return

    df = pd.read_csv(INPUT_CSV, sep=";", encoding="utf-8-sig", on_bad_lines='skip')
    
    if df.empty:
        print("🛑 Die Datei ist leer! Abbruch.")
        return

    # Spalten bereinigen
    # Spalten bereinigen (inkl. Fragezeichen!)
    df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_').str.replace('(', '').str.replace(')', '').str.replace('/', '_').str.replace('?', '')

    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)

    print(f"☁️ Sende {len(df)} Zeilen an {BIGQUERY_TABLE}...")
    
    try:
        job = client.load_table_from_dataframe(df, BIGQUERY_TABLE, job_config=job_config, location="EU")
        job.result()  
        print(f"\n🎉 ERFOLG! Die CSV wurde erfolgreich als Tabelle in die Cloud geladen!")
    except Exception as e:
        print(f"\n❌ Fehler beim Upload: {e}")

if __name__ == "__main__":
    upload()