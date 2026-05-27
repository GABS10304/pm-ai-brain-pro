import pandas as pd
import os
import csv
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. SETUP & CLOUD MOTOR
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_A = os.path.join(BASE_DIR, "tickets_a.csv")
FILE_B = os.path.join(BASE_DIR, "tickets_b.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Schnelles_PM_Backlog.csv")
DELIMITER = ";"

# HIER KOMMT DER IONOS MOTOR REIN:
IONOS_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiI0ZmIxYmQ1Ny1kZTE0LTRjY2QtOGRhNC03ZDNkODkzMGNjMTEiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJDb25Tb2wgQ29uc3VsdGluZyAmIFNvbHV0aW9ucyBTb2Z0d2FyZSBHbWJIIiwiaWF0IjoxNzc5MTk4NTI1LCJjbGllbnQiOiJVU0VSIiwiaWRlbnRpdHkiOnsiaXNQYXJlbnQiOmZhbHNlLCJjb250cmFjdE51bWJlciI6MzI0OTIzNDAsInJvbGUiOiJ1c2VyIiwicmVnRG9tYWluIjoiaW9ub3MuZGUiLCJyZXNlbGxlcklkIjo5MzM3NzIwNiwidXVpZCI6IjE2YzU2MGNkLWEyNjctNDlhYi04ZDUyLWVjOGE0ZTJkMzI4ZiIsInByaXZpbGVnZXMiOlsiQUNDRVNTX0FORF9NQU5BR0VfQUlfTU9ERUxfSFVCIl19LCJleHAiOjE4MTA3MzQ1MjV9.TBp-2dwuNu_-uNtiURWdMesdsNeinQrNgoiQj962qUvPuY2wVQEw069NSd3kit6Jz2RAyUX2kexCMWs3QQgyFPLDVdk0dp5MXigyJgCjbdv8OF2Y0Ev-th7GaAoICfpR--Bp9JmFNBzymz9Mbnl_TbDUdGHrAlfeZHH0U_suHkfenHpt0TebC0V-i7tG0sb9TbRuZM4TuQkBHWjb9OZpuVDQjOffQ9eb5x-LGr0ym0qF0QtFtRgHwE34lk1u6DXEi1q3S4tHBLpQh-JGWveyBsr4MaVaszb_AoaWDF1ol7diwTfQBrmwJhP-jvD2KCdVRcYHNNRJW0U2peAdRgXbCg" 

llm = ChatOpenAI(
    api_key=IONOS_TOKEN,
    base_url="https://openai.inference.de-txl.ionos.com/v1",
    model="openai/gpt-oss-120b", 
    temperature=0.0
)

# ==========================================
# 2. DATENSCHUTZ (LOCAL-FIRST) & KI-PROMPT
# ==========================================
def scrub_pii(text):
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL ENTFERNT]', text)
    text = re.sub(r'(?:\+49|0)[1-9][0-9\s\-\/]{7,}', '[TELEFON ENTFERNT]', text)
    text = re.sub(r'DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}', '[IBAN ENTFERNT]', text)
    return text

# Der clevere Senior-Prompt zwingt die KI zur Kategorisierung!
prompt = """Du bist Product Manager für eine Software. Analysiere dieses Feedback.

Regel 1: Wenn es nur "Alles gut", "Keine", "passt" ist, antworte EXAKT mit dem Wort: IRRELEVANT
Regel 2: Wenn es Relevanz hat, ordne es ZWINGEND in eine dieser 4 Kategorien ein: [Bug/Performance, Usability, Feature-Wunsch, Service/Schulung].

Antworte EXAKT in diesem Format (mit dem Symbol | dazwischen):
KATEGORIE: [Deine Kategorie] | TEXT: [Fasse das Problem in 1 Satz zusammen]

FEEDBACK:
{freitext}
"""
prompt_template = ChatPromptTemplate.from_template(prompt)
chain = prompt_template | llm

# ==========================================
# 3. DIE IONOS-CLOUD PIPELINE
# ==========================================
def process_fast_csv(filepath: str, customer_col: int, freitext_col: int, source_name: str) -> list:
    results = []
    if not os.path.exists(filepath):
        print(f"⚠️ Datei nicht gefunden: {os.path.basename(filepath)}")
        return results

    print(f"\n🚀 Sende {os.path.basename(filepath)} zur Analyse nach Berlin (IONOS)...")
    
    with open(filepath, mode='r', encoding='utf-8-sig', errors='replace') as file:
        reader = csv.reader(file, delimiter=DELIMITER)
        next(reader, None) # Kopfzeile überspringen
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) <= freitext_col: continue
                
            kunde = row[customer_col].strip() if len(row) > customer_col else f"Zeile {row_num}"
            freitext = row[freitext_col].strip()
            
            if not freitext or len(freitext) < 5 or freitext.lower() in ["nein", "keine", "-", "alles gut", "nichts", "passt"]:
                continue
                
            freitext = scrub_pii(freitext) # Datenschutz BEVOR es in die Cloud geht!
            
            print(f"   ☁️ KI analysiert: {kunde[:20]}...")
            
            try:
                # Da es ein ChatModel ist, müssen wir .content abgreifen
                antwort_text = chain.invoke({"freitext": freitext}).content.strip()
                
                if antwort_text != "IRRELEVANT" and "|" in antwort_text:
                    # Wir zerschneiden die saubere KI-Antwort in unsere SQL-Spalten
                    parts = antwort_text.split("|")
                    kat = parts[0].replace("KATEGORIE:", "").strip()
                    desc = parts[1].replace("TEXT:", "").strip()
                    
                    results.append({
                        "Kunde": kunde,
                        "Kategorie": kat,
                        "Original-Wortlaut (Freitext)": desc,
                        "Quelle": source_name
                    })
                    print(f"      ✅ [{kat}] gefunden!")
                else:
                    print("      🚮 Irrelevant.")
            except Exception as e:
                print(f"      ⚠️ Fehler: {e}")
                
    return results

# ==========================================
# 4. START & EXPORT
# ==========================================
if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, mode='a', encoding='utf-8-sig') as f_test: pass 
        except PermissionError:
            print(f"\n🛑 STOPP! Die Datei '{os.path.basename(OUTPUT_FILE)}' ist in Excel geöffnet!")
            exit()

    final_backlog = []
    
    final_backlog.extend(process_fast_csv(FILE_A, customer_col=0, freitext_col=3, source_name="Kundenumfrage (A)"))
    final_backlog.extend(process_fast_csv(FILE_B, customer_col=1, freitext_col=16, source_name="NPS Umfrage (B)"))

    if final_backlog:
        keys = final_backlog[0].keys()
        with open(OUTPUT_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys, delimiter=';')
            writer.writeheader()
            writer.writerows(final_backlog)
        print("\n🎉 FERTIG! Hochintelligente KI-Extraktion abgeschlossen.")
    else:
        print("\n🤷 Keine relevanten Freitexte gefunden.")