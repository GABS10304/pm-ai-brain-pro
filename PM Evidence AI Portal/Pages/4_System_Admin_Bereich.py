import streamlit as st
import subprocess
import os
import sys
import urllib.request
from urllib.error import HTTPError, URLError

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="Admin & Pipeline", page_icon="⚙️", layout="wide")
st.title("⚙️ Data Pipeline & Cloud Health")
st.markdown("Verwalte deine automatisierten Auswertungen und Cloud-Uploads direkt von hier.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# 2. SYSTEM HEALTH CHECKS
# ==========================================
st.subheader("🏥 System-Status")
col1, col2 = st.columns(2)

with col1:
    try:
        urllib.request.urlopen("https://openai.inference.de-txl.ionos.com/v1", timeout=3)
        st.success("IONOS KI-Cloud (Berlin/de-txl): ONLINE 🟢")
    except HTTPError as e:
        # Wenn der Server 401, 403 oder 404 funkt, heißt das: Er lebt, er will nur ein Passwort!
        if e.code in [401, 403, 404]:
            st.success("IONOS KI-Cloud (Berlin/de-txl): ONLINE 🟢")
        else:
            st.warning(f"Verbindungsproblem mit IONOS (Fehlercode {e.code}) 🔴")
    except URLError:
        st.warning("Kein Internet: Kann die IONOS Server nicht erreichen 🔴")

with col2:
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
st.subheader("🚀 Cloud-Skripte ausführen")

def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)
    if not os.path.exists(script_path):
        st.error(f"Skript {script_name} nicht gefunden unter {script_path}!")
        return

    log_area = st.empty()
    logs = f"Starte {script_name}...\n{'='*50}\n"
    log_area.code(logs, language="bash")

     # NEU: Wir packen den "Emoji-Schutz" für Windows in die Umgebung
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"

    # Startet das Skript im Hintergrund
    process = subprocess.Popen(
        [sys.executable, script_path], 
        cwd=BASE_DIR, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True,
        encoding='utf-8',
        errors='replace',
        env=my_env  # HIER wird das Emoji-Schutzschild mitgegeben!
    )

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
    if st.button("🚀 IONOS: CSV-Pumpe (rag.py)", use_container_width=True):
        run_script("rag.py")
    if st.button("🚀 IONOS: HTML-Schredder", use_container_width=True):
        run_script("html_schredder.py")

with colB:
    st.markdown("**Schritt 2: Zusammenfassen (Epics)**")
    if st.button("🚀 IONOS: Strategie-Aggregator", use_container_width=True):
        run_script("batch_aggregator.py")

with colC:
    st.markdown("**Schritt 3: Cloud & Dashboarding**")
    if st.button("☁️ Push zu Google BigQuery", use_container_width=True):
        run_script("bq_uploader.py")