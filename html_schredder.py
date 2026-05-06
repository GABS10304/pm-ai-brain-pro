import os
import csv
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FOLDER = os.path.join(BASE_DIR, "data", "html") 
OUTPUT_CSV = os.path.join(BASE_DIR, "HTML_Tickets_Fertig_fuer_Copilot.csv")

# Schnelles Modell ohne automatische Pydantic-JSON-Schleifen
llm = OllamaLLM(model="llama3.2", temperature=0.0)

# ==========================================
# 2. DER ZUVERLÄSSIGE FILTER-PROMPT
# ==========================================
prompt = """Du bist Product Manager für unsere B2B-Software.
Lies dieses Support-Ticket, ignoriere Signaturen und E-Mail-Verläufe und finde den Kern des Software-Problems.

Regel 1: Wenn es reiner Support-Alltag (Passwort-Reset, Neustart, Druckerprobleme, Danke) ist, antworte EXAKT mit dem Wort: IRRELEVANT
Regel 2: Wenn ein echter Bug, ein Workaround, ein fehlendes Feature oder ein Usability-Problem beschrieben wird, antworte in 1-2 Sätzen mit der Kernbeschreibung des Problems.

TICKET-TEXT:
{ticket_text}
"""

prompt_template = ChatPromptTemplate.from_template(prompt)
chain = prompt_template | llm

# ==========================================
# 3. DIE SCHREDDER-MASCHINE
# ==========================================
def shredder():
    print(f"\n🚜 Starte HTML-Schredder im robusten Plain-Text-Modus...\n")
    ergebnisse = []
    
    if not os.path.exists(HTML_FOLDER):
        print(f"⚠️ Ordner nicht gefunden: {HTML_FOLDER}")
        return

    # === PRE-FLIGHT CHECK (Die Excel-Schutzschranke) ===
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, mode='a', encoding='utf-8-sig') as f_test:
                pass 
        except PermissionError:
            print("🛑 STOPP! FATALER FEHLER BEVOR ES LOSGEHT!")
            print(f"Die Zieldatei ist aktuell in Excel geöffnet!")
            print("Bitte schließe die CSV in Excel komplett und starte das Skript danach neu. Abbruch.")
            return
    # ===================================================

    for root, _, files in os.walk(HTML_FOLDER):
        for file in files:
            if file.lower().endswith(".html"):
                filepath = os.path.join(root, file)
                
                unterordner = os.path.relpath(root, HTML_FOLDER)
                if unterordner == ".": unterordner = "Hauptordner"
                
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        soup = BeautifulSoup(f, "lxml")
                        reiner_text = soup.get_text(separator=" ", strip=True) 
                        
                    if len(reiner_text) < 20: continue
                        
                    # Großzügige 3000 Zeichen (für Kundenprobleme weit unten im Verlauf)
                    text_snippet = reiner_text[:3000] 
                    
                    print(f"   ⏳ KI prüft (einmalig): [{unterordner}] {file[:25]}...")
                    
                    antwort_text = chain.invoke({"ticket_text": text_snippet}).strip()
                    
                    if antwort_text == "IRRELEVANT":
                        print("      🚮 Irrelevant / Support-Alltag.")
                    else:
                        print("      ✅ Problem erkannt & extrahiert!")
                        ergebnisse.append({
                            "Ordner / Modul": unterordner,
                            "Quelle (Dateiname)": file,
                            "Kategorie": "Ticket-Extrakt",
                            "Original-Wortlaut (Freitext)": antwort_text, 
                        })
                        
                except Exception as e:
                    print(f"      ⚠️ Fehler bei Datei {file}: {e}")

    # ==========================================
    # 4. EXPORT
    # ==========================================
    if ergebnisse:
        keys = ergebnisse[0].keys()
        with open(OUTPUT_CSV, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys, delimiter=';')
            writer.writeheader()
            writer.writerows(ergebnisse)
        print(f"\n🎉 BASECAMP ERREICHT! {len(ergebnisse)} Tickets sicher gerettet.")
    else:
        print("\n🤷 Keine relevanten Software-Probleme gefunden.")

if __name__ == "__main__":
    shredder()