import streamlit as st

# ==========================================
# 1. SETUP & PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="RIWA AI Pro Suite",
    page_icon="🏢",
    layout="wide"
)

# Der Architektur-Badge oben links
st.markdown("[![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20(Local%20AI%20+%20Cloud%20SQL)-blue)](#)")

st.title("Willkommen in der RIWA AI Pro Suite 🚀")
st.markdown("Deine interne Werkzeugkiste für datengetriebene Entscheidungen. Wähle unten das passende Tool für deine heutige Aufgabe aus:")

st.divider()

# ==========================================
# 2. DIE SUITE (APP-STORE LAYOUT)
# ==========================================
col1, col2 = st.columns(2)

# --- REIHE 1 ---
with col1:
    st.info("### 📊 1. Product Feedback Dashboard")
    st.write("**Aufgabe:** Du willst die 'Voice of the Customer' verstehen.")
    st.write("- Zieht harte Zahlen live aus deinen BigQuery-Tabellen.")
    st.write("- Vereint strukturierte Umfragen (NPS/CSVs) und geschredderte Support-Tickets (HTML).")
    st.write("- Liefert dir fertige, priorisierte Produkt-Epics aus dem Analysten-Skript.")
    st.write("- **Zielgruppe:** Product Manager, Support Leads, UX-Designer.")

with col2:
    st.success("### 💼 2. Sales Strategy Tool")
    st.write("**Aufgabe:** Du musst Vetriebs-Strategien oder ICPs festlegen.")
    st.write("- Rechnet Verträge, Netto-Werte und Preise datenschutzkonform in Python aus.")
    st.write("- KI generiert ein Sales Cheat-Sheet aus harten Rabatt-Zahlen.")
    st.write("- **Zielgruppe:** Revenue Operations, Sales Management.")

st.markdown("<br>", unsafe_allow_html=True) # Etwas Abstand für ein sauberes Layout

# --- REIHE 2 ---
col3, col4 = st.columns(2)

with col3:
    st.warning("### 🧠 3. Freier KI-Chat (Copilot)")
    st.write("**Aufgabe:** Du hast spezielle Rohdaten und offene Fragen.")
    st.write("- Lade eine x-beliebige eigene CSV-Datei (z.B. neue Umfragen) hoch.")
    st.write("- Die RAG-Architektur macht deine Datei in 5 Sekunden durchsuchbar.")
    st.write("- Chatte mit der KI wie mit einem Analysten über diese Daten.")
    st.write("- **Zielgruppe:** Analysten, PMs im Deep-Dive.")

with col4:
    st.error("### ⚙️ 4. System Admin Bereich")
    st.write("**Aufgabe:** Daten aufbereiten und in die Cloud pushen.")
    st.write("- Der IT-Maschinenraum deines Portals.")
    st.write("- Hier laufen die Schredder-, Filter- und Aggregator-Skripte im Hintergrund.")
    st.write("- **Bitte nur betreten, wenn du frische Rohdaten für das Dashboard verarbeiten willst!**")

st.divider()
st.markdown("<small><i>Architektur: Hybrides Setup (Lokal laufende Ollama LLMs + Google BigQuery Anbindung). Datenschutzkonform nach DSGVO.</i></small>", unsafe_allow_html=True)