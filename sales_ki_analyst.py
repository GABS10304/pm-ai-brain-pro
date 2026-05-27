import pandas as pd
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Das Skript holt sich automatisch die Datei, die wir oben generiert haben!
INPUT_FILE = os.path.join(BASE_DIR, "Sales_ICP_Strategie_Daten.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Sales_Strategie_Report.md")

# ==========================================
# IONOS CLOUD MOTOR
# ==========================================
IONOS_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiI0ZmIxYmQ1Ny1kZTE0LTRjY2QtOGRhNC03ZDNkODkzMGNjMTEiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJDb25Tb2wgQ29uc3VsdGluZyAmIFNvbHV0aW9ucyBTb2Z0d2FyZSBHbWJIIiwiaWF0IjoxNzc5MTk4NTI1LCJjbGllbnQiOiJVU0VSIiwiaWRlbnRpdHkiOnsiaXNQYXJlbnQiOmZhbHNlLCJjb250cmFjdE51bWJlciI6MzI0OTIzNDAsInJvbGUiOiJ1c2VyIiwicmVnRG9tYWluIjoiaW9ub3MuZGUiLCJyZXNlbGxlcklkIjo5MzM3NzIwNiwidXVpZCI6IjE2YzU2MGNkLWEyNjctNDlhYi04ZDUyLWVjOGE0ZTJkMzI4ZiIsInByaXZpbGVnZXMiOlsiQUNDRVNTX0FORF9NQU5BR0VfQUlfTU9ERUxfSFVCIl19LCJleHAiOjE4MTA3MzQ1MjV9.TBp-2dwuNu_-uNtiURWdMesdsNeinQrNgoiQj962qUvPuY2wVQEw069NSd3kit6Jz2RAyUX2kexCMWs3QQgyFPLDVdk0dp5MXigyJgCjbdv8OF2Y0Ev-th7GaAoICfpR--Bp9JmFNBzymz9Mbnl_TbDUdGHrAlfeZHH0U_suHkfenHpt0TebC0V-i7tG0sb9TbRuZM4TuQkBHWjb9OZpuVDQjOffQ9eb5x-LGr0ym0qF0QtFtRgHwE34lk1u6DXEi1q3S4tHBLpQh-JGWveyBsr4MaVaszb_AoaWDF1ol7diwTfQBrmwJhP-jvD2KCdVRcYHNNRJW0U2peAdRgXbCg" 

llm = ChatOpenAI(
    api_key=IONOS_TOKEN,
    base_url="https://openai.inference.de-txl.ionos.com/v1",
    model="openai/gpt-oss-120b", 
    temperature=0.0
)

# ==========================================
# 2. DIE ANALYSE
# ==========================================
def analyze_sales():
    print("\n🚀 Starte den KI-Analysten für deine RevOps & ICP Daten...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"⚠️ Die Datei {INPUT_FILE} wurde nicht gefunden!")
        print("Bitte führe zuerst das Datenskript 'sales_prep.py' aus.")
        return

    # Lade die bereinigten Daten
    df = pd.read_csv(INPUT_FILE, sep=";", encoding="utf-8-sig")
    
    # Nimm nur die Top 50 Ergebnisse (die wichtigsten Segmente), um die KI nicht zu überladen
    daten_text = df.head(50).to_markdown(index=False)

    prompt = ChatPromptTemplate.from_template("""
    Du bist der Head of Revenue Operations und Sales Strategist in einer B2B Software-Firma für Kommunen (GovTech).
    Hier ist eine fertig berechnete, 100% anonymisierte Tabelle unserer Verkäufe, sortiert nach unserem 'ICP_Score'.
    
    Analysiere diese Tabelle knallhart und erstelle ein 'Sales Cheat Sheet' für unser Vertriebsteam.
    Nutze ZWINGEND dieses Format zur Beantwortung:
    
    ### 🥇 1. Unser Traumkunde (Ideal Customer Profile)
    Welche Kombination aus Kundentyp und Modul sichert uns das wichtigste Geschäft? Begründe warum.
    
    ### 💸 2. Preis-Strategie (Rabatte)
    Wo lassen wir aktuell Geld auf dem Tisch liegen? In welchem Segment/Modul geben wir viel zu hohe Rabatte, obwohl wir das nicht müssten?
    
    ### 📈 3. Verstecktes Potenzial
    Gibt es Segmente mit hoher Käufer-Anzahl, aber erstaunlich niedrigem Gesamt-Volumen? Hier müssen wir Cross-Selling betreiben.
    
    ### 🎯 4. Deine 3 Sales-To-Dos
    Nenne 3 messerscharfe, sofort anwendbare Handlungsanweisungen für den Vertrieb in der nächsten Woche.
    
    ROHDATEN-TABELLE ZUR ANALYSE:
    {daten}
    """)

    print("🧠 Qwen studiert gerade deine ICP-Matrix. Bitte warten...")
    
    chain = prompt | llm
    ergebnis = chain.invoke({"daten": daten_text})

    # Exportieren als lesbares Markdown-Dokument
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        f.write(ergebnis)

    print("\n============================================================")
    print("🎉 FERTIG! Dein fundiertes Sales Cheat Sheet ist bereit!")
    print("============================================================\n")
    print(ergebnis)
    print(f"\n📁 Speicherung erfolgreich: Die Datei liegt bereit unter {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_sales()