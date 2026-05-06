import csv
import os
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# ==================================================
# 1. SETUP & PATH-KONFIGURATION
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_A = os.path.join(BASE_DIR, "tickets_a.csv")
FILE_B = os.path.join(BASE_DIR, "tickets_b.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Schnelles_PM_Backlog.csv")

DELIMITER = ";"

# Dein lokales Modell (Meta's schnelles 3-Milliarden-Parameter Modell)
llm = ChatOllama(model="llama3.2", temperature=0.0, format="json")

# ==================================================
# 2. DAS PYDANTIC MODELL (Striktes Regelwerk)
# ==================================================
class PMInsight(BaseModel):
    kategorie: str = Field(default="Keine", description="MUSST du aus dieser Liste wählen: 'Feature-Wunsch', 'Bug', 'Usability', 'Prozess/Schulung'.")
    ticket_titel: str = Field(default="", description="Maximal 5-7 Worte. z.B. 'Webinare für Updates anbieten' oder 'Darstellung Bauanträge anpassen'.")
    pm_zusammenfassung: str = Field(default="", description="Keine Floskeln! Nenne konkret in 1-2 Sätzen, welches Feature oder welcher Prozess laut Nutzer fehlt oder gebaut werden muss.")

structured_llm = llm.with_structured_output(PMInsight)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Du bist ein extrem analytischer, knallharter Product Manager für B2B-Software.
    Regeln:
    1. Fasse den Schmerzpunkt des Nutzers kurz zusammen.
    2. Keine leeren Phrasen wie 'Wir müssen eine Lösung finden'. Sag konkret, WAS gemacht werden muss.
    3. Nutze für den Titel maximal 7 Worte!
    """),
    ("human", "Lese diesen Text und leite ein To-Do ab:\n{freitext}")
])

chain = prompt_template | structured_llm

# ==================================================
# 3. DIE TURBO-VERARBEITUNG
# ==================================================
def process_fast_csv(filepath: str, customer_col: int, freitext_col: int, source_name: str) -> list:
    results = []
    
    if not os.path.exists(filepath):
        print(f"⚠️ Datei nicht gefunden: {filepath}")
        return results

    print(f"\n🚀 Turbo-Scan für {filepath} (Nur Freitexte)...")
    
    with open(filepath, mode='r', encoding='utf-8-sig', errors='replace') as file:
        reader = csv.reader(file, delimiter=DELIMITER)
        next(reader, None) # Kopfzeile überspringen
        
        for row_num, row in enumerate(reader, start=2):
            
            # Sicherheitscheck: Hat die Zeile überhaupt so viele Spalten?
            if len(row) <= freitext_col:
                continue
                
            kunde = row[customer_col].strip() if len(row) > customer_col else f"Zeile {row_num}"
            freitext = row[freitext_col].strip()
            
            # HIER FINDET DIE MAGIE STATT: Müll sofort blockieren!
            if not freitext or len(freitext) < 5 or freitext.lower() in ["nein", "keine", "-", "alles gut", "nichts", "passt"]:
                # Skript springt zur nächsten Zeile, ohne die KI zu wecken!
                continue
                
            print(f"   🧠 KI analysiert echten Freitext von: {kunde[:20]}...")
            
            try:
                # KI bekommt NUR den relevanten Text!
                insight = chain.invoke({"freitext": freitext})

                results.append({
                    "Quelle": source_name,
                    "Kunde": kunde,
                    "Original-Wortlaut (Freitext)": freitext,
                    "Kategorie": insight.kategorie,
                    "Titel (Jira)": insight.ticket_titel,
                    "Was ist zu tun?": insight.pm_zusammenfassung
                })
                print(f"      ✅ Backlog-Item erstellt: {insight.ticket_titel}")
            except Exception as e:
                print(f"      ⚠️ Fehler: {e}")
                
    return results

# ==================================================
# 4. START & EXPORT
# ==================================================
if __name__ == "__main__":
    final_backlog = []
    
    # FILE A: Kunde ist Spalte A (0), Feedback ist Spalte D (3)
    final_backlog.extend(process_fast_csv(FILE_A, customer_col=0, freitext_col=3, source_name="Kundenumfrage (A)"))

    # FILE B: Kunde/Landkreis ist Spalte B (1), Feedback ist Spalte Q (16)
    final_backlog.extend(process_fast_csv(FILE_B, customer_col=1, freitext_col=16, source_name="NPS Umfrage (B)"))
    
    if final_backlog:
        print(f"\n💾 Speichere {len(final_backlog)} gefilterte Insights in '{OUTPUT_FILE}'...")
        keys = final_backlog[0].keys()
        
        with open(OUTPUT_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(final_backlog)
            
        print("🎉 FERTIG! Phase 1 (Extraktion) ist abgeschlossen. Öffne die CSV in Excel!")
    else:
        print("\n🤷 Keine relevanten Freitexte gefunden.")