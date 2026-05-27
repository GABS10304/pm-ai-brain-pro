import pandas as pd
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. SETUP & CLOUD MOTOR
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Liest die geschredderten HTML-Tickets!
INPUT_CSV = os.path.join(BASE_DIR, "HTML_Tickets_Fertig_fuer_Copilot.csv") 
OUTPUT_REPORT = os.path.join(BASE_DIR, "Finaler_PM_Report.md")

BATCH_SIZE = 50 

# HIER KOMMT DER IONOS MOTOR REIN:
IONOS_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiI0ZmIxYmQ1Ny1kZTE0LTRjY2QtOGRhNC03ZDNkODkzMGNjMTEiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJDb25Tb2wgQ29uc3VsdGluZyAmIFNvbHV0aW9ucyBTb2Z0d2FyZSBHbWJIIiwiaWF0IjoxNzc5MTk4NTI1LCJjbGllbnQiOiJVU0VSIiwiaWRlbnRpdHkiOnsiaXNQYXJlbnQiOmZhbHNlLCJjb250cmFjdE51bWJlciI6MzI0OTIzNDAsInJvbGUiOiJ1c2VyIiwicmVnRG9tYWluIjoiaW9ub3MuZGUiLCJyZXNlbGxlcklkIjo5MzM3NzIwNiwidXVpZCI6IjE2YzU2MGNkLWEyNjctNDlhYi04ZDUyLWVjOGE0ZTJkMzI4ZiIsInByaXZpbGVnZXMiOlsiQUNDRVNTX0FORF9NQU5BR0VfQUlfTU9ERUxfSFVCIl19LCJleHAiOjE4MTA3MzQ1MjV9.TBp-2dwuNu_-uNtiURWdMesdsNeinQrNgoiQj962qUvPuY2wVQEw069NSd3kit6Jz2RAyUX2kexCMWs3QQgyFPLDVdk0dp5MXigyJgCjbdv8OF2Y0Ev-th7GaAoICfpR--Bp9JmFNBzymz9Mbnl_TbDUdGHrAlfeZHH0U_suHkfenHpt0TebC0V-i7tG0sb9TbRuZM4TuQkBHWjb9OZpuVDQjOffQ9eb5x-LGr0ym0qF0QtFtRgHwE34lk1u6DXEi1q3S4tHBLpQh-JGWveyBsr4MaVaszb_AoaWDF1ol7diwTfQBrmwJhP-jvD2KCdVRcYHNNRJW0U2peAdRgXbCg" 

llm = ChatOpenAI(
    api_key=IONOS_TOKEN,
    base_url="https://openai.inference.de-txl.ionos.com/v1",
    model="openai/gpt-oss-120b", 
    temperature=0.0
)

# Beide Agenten nutzen jetzt IONOS-Power!
schneller_arbeiter = llm
kluger_stratege = llm

# ==========================================
# 2. DIE PROMPTS 
# ==========================================
map_prompt = ChatPromptTemplate.from_template("""
Analysiere die folgenden Kundenfeedbacks. 
Finde die 3 bis 5 am häufigsten genannten Software-Probleme.
Antworte STRIKT in diesem Format pro Problem (Keine Romane!):
- [Stichwort/Thema] - Kurzer Grund.

FEEDBACKS:
{chunk_text}
""")

reduce_prompt = ChatPromptTemplate.from_template("""
Du bist ein Senior Product Manager. Hier sind Zwischenergebnisse aus der Analyse von exakt {total_tickets} Kundenfeedbacks.
Deine Aufgabe:
Fasse diese Zwischenergebnisse zu einer finalen "TOP 5 EPICS" Liste zusammen. Fasse inhaltlich gleiche Themen zusammen.
Beginne deinen Report ZWINGEND mit genau diesem Satz: "Basierend auf der Analyse von {total_tickets} Tickets, sind hier die priorisierten Top 5 Problemfelder:"

ROHDATEN:
{alle_zusammenfassungen}
""")

map_chain = map_prompt | schneller_arbeiter
reduce_chain = reduce_prompt | kluger_stratege

# ==========================================
# 3. DER MAP-REDUCE PROZESS
# ==========================================
def run_aggregator():
    print("🚀 Starte den Map-Reduce Aggregator über IONOS Cloud...\n")
    
    if not os.path.exists(INPUT_CSV):
        print("⚠️ Eingabedatei nicht gefunden!")
        return

    df = pd.read_csv(INPUT_CSV, sep=";", encoding="utf-8-sig", on_bad_lines='skip')
    gesamt_zeilen = len(df)
    print(f"📊 {gesamt_zeilen} Zeilen gefunden. Teile in {BATCH_SIZE}er Blöcke auf...\n")

    feedbacks = df["Original-Wortlaut (Freitext)"].dropna().tolist()
    zwischen_ergebnisse = ""

    for i in range(0, len(feedbacks), BATCH_SIZE):
        chunk = feedbacks[i:i + BATCH_SIZE]
        chunk_text = "\n".join([f"- {text}" for text in chunk])
        
        print(f"   ⏳ Wolke analysiert Zeile {i + 1} bis {min(i + BATCH_SIZE, gesamt_zeilen)}...")
        
        try:
            # Hier nutzt er das ChatOpenAI Interface, um den Content herauszuziehen
            ergebnis = map_chain.invoke({"chunk_text": chunk_text}).content
            zwischen_ergebnisse += f"\n--- Batch {i+1} ---\n{ergebnis}\n"
        except Exception as e:
            print(f"      ⚠️ Fehler im Batch {i}: {e}")

    # ==========================================
    # DER SPION-CHECK
    # ==========================================
    print("\n🧠 Alle Blöcke analysiert! Übergebe Notizzettel an die Chef-KI...")
    print(f"🕵️‍♂️ SPION-CHECK: Der gesammelte Cloud-Text hat {len(zwischen_ergebnisse)} Zeichen!")
    print("   Bitte warten, die Master-Analyse wird in der IONOS-Cloud geschrieben...\n")
    
    # Wir übergeben die Daten an IONOS
    final_response = reduce_chain.invoke({
        "alle_zusammenfassungen": zwischen_ergebnisse,
        "total_tickets": gesamt_zeilen
    })
    
    # Text vom Cloud-Ergebnis trennen
    finaler_report = final_response.content
    
    # Exportieren
    with open(OUTPUT_REPORT, mode="w", encoding="utf-8-sig") as f:
        f.write(finaler_report)
        
    print("="*50)
    print("🎉 FERTIG! DEIN CLOUD-REPORT IST DA!")
    print("="*50)
    print(finaler_report)

if __name__ == "__main__":
    run_aggregator()