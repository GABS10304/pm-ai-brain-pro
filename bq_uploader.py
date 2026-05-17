import os
import pandas as pd
from google.cloud import bigquery

# ==========================================
# 1. SETUP & AUTHENTIFIKATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "gcp-key.json")

# HIER IST DEINE GEWÜNSCHTE DATEI:
INPUT_CSV = os.path.join(BASE_DIR, "HTML_Tickets_Fertig_fuer_Copilot.csv")

# 🚨 Neuer Tabellenname für die HTML-Tickets!
BIGQUERY_TABLE = "pm-analytics-496606.pm_daten.html_tickets_rohdaten"

DELIMITER = ";"

# ==========================================
# 2. UPLOAD-FUNKTION
# ==========================================
def upload_html_tickets_to_bigquery():
    print(f"🚀 Starte BigQuery-Upload für HTML-Tickets...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"⚠️ Datei {INPUT_CSV} nicht gefunden!")
        return

    df = pd.read_csv(INPUT_CSV, sep=DELIMITER, encoding="utf-8-sig", on_bad_lines='skip')
    
    # Spaltennamen SQL-sicher machen (er macht z.B aus 'Ordner / Modul' -> 'Ordner___Modul')
    df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_').str.replace('(', '').str.replace(')', '').str.replace('/', '_')

    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

    print(f"☁️ Sende {len(df)} geschredderte Tickets an: {BIGQUERY_TABLE}...")
    
    try:
        job = client.load_table_from_dataframe(df, BIGQUERY_TABLE, job_config=job_config)
        job.result() 
        
        table = client.get_table(BIGQUERY_TABLE)
        print(f"\n🎉 ERFOLG! Die Datei ist hochgeladen. Die Tabelle hat jetzt {table.num_rows} Zeilen.")
    
    except Exception as e:
        print(f"\n❌ Fehler beim Upload: {e}")

if __name__ == "__main__":
    upload_html_tickets_to_bigquery()