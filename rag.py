import pandas as pd
import os
import csv
import re
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. SETUP & PFADE
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_A = os.path.join(BASE_DIR, "tickets_a.csv")
FILE_B = os.path.join(BASE_DIR, "tickets_b.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Schnelles_PM_Backlog.csv")

DELIMITER = ";"

# Schnelles Modell ohne Absturz-gefährdete JSON-Schleifen
llm = OllamaLLM(model="llama3.2", temperature=0.0)

# ==========================================
# 2. DATENSCHUTZ & FILTER-REGELN
# ==========================================
def scrub_pii(text):
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL ENTFERNT]', text)
    text = re.sub(r'(?:\+49|0)[1-9][0-9\s\-\/]{7,}', '[TELEFON ENTFERNT]', text)
    text = re.sub(r'DE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}', '[IBAN ENTFERNT]', text)
    return text

prompt = """Du bist Product Manager für eine GIS-Software. Lies dieses Kundenfeedback.

Regel 1: Wenn es nur Floskeln sind ("Alles gut", "Nein", "Keine", "Weiter so") oder unverständlicher Müll, antworte EXAKT mit dem Wort: IRRELEVANT
Regel 2: Wenn ein echter Wunsch, Bug oder eine Kritik drinsteckt, fasse das Kernproblem in 1 bis 2 Sätzen sauber zusammen.

KUNDEN-FEEDBACK:
{freitext}
"""
prompt_template = ChatPromptTemplate.from_template(prompt)
chain = prompt_template | llm

# ==========================================
# 3. DIE TURBO-VERARBEITUNG
# ==========================================
def process_fast_csv(filepath: str, customer_col: int, freitext_col: int, source_name: str) -> list:
    results = []
    if not os.path.exists(filepath):
        print(f"⚠️ Datei nicht gefunden: {filepath}")
        return results

    print(f"\n🚀 Turbo-Scan für {os.path.basename(filepath)}...")
    
    with open(filepath, mode='r', encoding='utf-8-sig', errors='replace') as file:
        reader = csv.reader(file, delimiter=DELIMITER)
        next(reader, None) # Kopfzeile überspringen
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) <= freitext_col:
                continue
                
            kunde = row[customer_col].strip() if len(row) > customer_col else f"Zeile {row_num}"
            freitext = row[freitext_col].strip()
            
            # Harte Müll-Ausfilterung vor dem KI-Aufruf
            if not freitext or len(freitext) < 5 or freitext.lower() in ["nein", "keine", "-", "alles gut", "nichts", "passt"]:
                continue
                
            # 🛡️ DATENSCHUTZ-FILTER AKTIVIEREN
            freitext = scrub_pii(freitext)
            
            print(f"   🧠 KI analysiert: {kunde[:20]}...")
            
            try:
                antwort_text = chain.invoke({"freitext": freitext}).strip()
                
                if antwort_text != "IRRELEVANT":
                    results.append({
                        "Ordner / Modul": "Umfrage", # Einheitlich zum Schredder
                        "Quelle (Dateiname)": source_name,
                        "Kategorie": "Umfrage-Extrakt",
                        "Original-Wortlaut (Freitext)": antwort_text
                    })
                    print("      ✅ Insight extrahiert!")
                else:
                    print("      🚮 Irrelevant.")
            except Exception as e:
                print(f"      ⚠️ Fehler bei der Auswertung: {e}")
                
    return results

# ==========================================
# 4. START & EXPORT
# ==========================================
if __name__ == "__main__":
    
    # 🛡️ PRE-FLIGHT CHECK: Ist Excel geschlossen?
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, mode='a', encoding='utf-8-sig') as f_test: 
                pass 
        except PermissionError:
            print("\n🛑 STOPP! FATALER FEHLER BEVOR ES LOSGEHT!")
            print(f"Die Datei '{os.path.basename(OUTPUT_FILE)}' ist aktuell in Excel geöffnet!")
            print("Bitte schließe Excel komplett und starte das Skript danach neu. Abbruch.")
            exit()

    final_backlog = []
    
    # Datei A und B nacheinander pumpen
    final_backlog.extend(process_fast_csv(FILE_A, customer_col=0, freitext_col=3, source_name="Kundenumfrage (A)"))
    final_backlog.extend(process_fast_csv(FILE_B, customer_col=1, freitext_col=16, source_name="NPS Umfrage (B)"))

    if final_backlog:
        keys = final_backlog[0].keys()
        with open(OUTPUT_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys, delimiter=';')
            writer.writeheader()
            writer.writerows(final_backlog)
        print("\n🎉 FERTIG! Phase 1 (Extraktion) ist datenschutzsicher abgeschlossen.")
    else:
        print("\n🤷 Keine relevanten Freitexte gefunden.")