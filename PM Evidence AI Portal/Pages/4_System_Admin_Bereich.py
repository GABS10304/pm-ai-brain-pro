import streamlit as st
import subprocess
import os
import urllib.request

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="Admin & Pipeline", page_icon="⚙️", layout="wide")
st.title("⚙️ Data Pipeline & System Health")
st.markdown("Verwalte deine lokalen KI-Agenten und Cloud-Uploads direkt von hier aus.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# 2. SYSTEM HEALTH CHECKS
# ==========================================
st.subheader("🏥 System-Status")
col1, col2 = st.columns(2)

with col1:
    # Prüft, ob der KI-Motor im Hintergrund surrt
    try:
        urllib.request.urlopen("http://localhost:11434/", timeout=2)
        st.success("KI-Motor (Ollama): ONLINE 🟢")
    except:
        st.error("KI-Motor (Ollama): OFFLINE 🔴 (Bitte Ollama starten!)")

with col2:
    # Prüft hartnäckige Excel-Blockaden
    files_to_check = ["Schnelles_PM_Backlog.csv", "HTML_Tickets_Fertig_fuer_Copilot.csv", "Finaler_PM_Report.md"]
    locked_files = []
    
    for f in files_to_check:
        filepath = os.path.join(BASE_DIR, f)
        if os.path.exists(filepath):
            try:
                with open(filepath, mode='a'): pass
            except PermissionError:
                locked_files.append(f)
                
    if locked_files:
        st.error(f"Dateien in Excel blockiert 🔴: {', '.join(locked_files)}")
    else:
        st.success("Datei-Zugriff (Schreibrechte): FREI 🟢")

st.divider()

# ==========================================
# 3. PIPELINE STEUERUNG (LIVE TERMINAL)
# ==========================================
st.subheader("🚀 Skripte ausführen")

# Diese Funktion baut unsichtbar eine Brücke zwischen Webseite und Betriebssystem!
def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    if not os.path.exists(script_path):
        st.error(f"Skript {script_name} nicht gefunden unter {script_path}!")
        return

    # Box für die Live-Meldungen auf der Webseite
    log_area = st.empty()
    logs = f"Starte {script_name}...\n{'='*50}\n"
    log_area.code(logs, language="bash")

    # Startet das Skript im Hintergrund
    process = subprocess.Popen(
        ["python", script_path], 
        cwd=BASE_DIR, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    # Liest jede Zeile, die das Skript spuckt, live in die App
    for line in iter(process.stdout.readline, ''):
        if line:
            logs += line
            log_area.code(logs, language="bash")
    
    process.stdout.close()
    process.wait()
    logs += f"\n{'='*50}\nProzess beendet!"
    log_area.code(logs, language="bash")
    
    if process.returncode == 0:
        st.toast(f"✅ {script_name} erfolgreich beendet!")
    else:
        st.toast(f"⚠️ Fehler in {script_name} aufgetreten.")

colA, colB, colC = st.columns(3)

with colA:
    st.markdown("**Schritt 1: Entrauschen & Filtern**")
    if st.button("▶️ Müllabfuhr starten (rag.py)", use_container_width=True):
        run_script("rag.py")
    if st.button("▶️ HTML-Schredder starten", use_container_width=True):
        run_script("html_schredder.py")

with colB:
    st.markdown("**Schritt 2: Zusammenfassen (Epics)**")
    if st.button("▶️ Strategie-Agent (Aggregator)", use_container_width=True):
        run_script("batch_aggregator.py")

with colC:
    st.markdown("**Schritt 3: Cloud & Dashboarding**")
    if st.button("☁️ Push zu Google BigQuery", use_container_width=True):
        run_script("bq_uploader.py")