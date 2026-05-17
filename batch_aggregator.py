import pandas as pd
import os
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Liest die geschredderten HTML-Tickets!
INPUT_CSV = os.path.join(BASE_DIR, "HTML_Tickets_Fertig_fuer_Copilot.csv") 
OUTPUT_REPORT = os.path.join(BASE_DIR, "Finaler_PM_Report.md")

BATCH_SIZE = 50 

# Beide Modelle mit großem Speicher (num_ctx) initialisieren
schneller_arbeiter = OllamaLLM(model="llama3.2", temperature=0.0, num_ctx=8192)
kluger_stratege = OllamaLLM(model="llama3.2", temperature=0.0, num_ctx=8192)

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
    print("🚀 Starte den Map-Reduce Aggregator für riesige CSV Dateien...\n")
    
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
        
        print(f"   ⏳ Arbeiter (llama) analysiert Zeile {i + 1} bis {min(i + BATCH_SIZE, gesamt_zeilen)}...")
        
        try:
            ergebnis = map_chain.invoke({"chunk_text": chunk_text})
            zwischen_ergebnisse += f"\n--- Batch {i+1} ---\n{ergebnis}\n"
        except Exception as e:
            print(f"      ⚠️ Fehler im Batch {i}: {e}")

    # ==========================================
    # DER SPION-CHECK
    # ==========================================
    print("\n🧠 Alle Blöcke analysiert! Übergebe Notizzettel an den Strategen (Qwen)...")
    print(f"🕵️‍♂️ SPION-CHECK: Der gesammelte Llama-Text hat {len(zwischen_ergebnisse)} Zeichen!")
    print("   Bitte warten, die Master-Analyse wird geschrieben...\n")
    
    # Wir übergeben dem Chef-Prompter jetzt die exakte Total-Zahl!
    finaler_report = reduce_chain.invoke({
        "alle_zusammenfassungen": zwischen_ergebnisse,
        "total_tickets": gesamt_zeilen
    })
    
    # Exportieren als lesbare Text/Markdown-Datei
    with open(OUTPUT_REPORT, mode="w", encoding="utf-8-sig") as f:
        f.write(finaler_report)
        
    print("="*50)
    print("🎉 FERTIG! DEIN REPORT IST DA!")
    print("="*50)
    print(finaler_report)

if __name__ == "__main__":
    run_aggregator()