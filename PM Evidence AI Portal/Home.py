import streamlit as st

# Seiteneinstellung für das gesamte Portal (Ohne Firmennamen)
st.set_page_config(
    page_title="PM AI Brain Pro Suite",
    page_icon="🧠",
    layout="wide"
)

# Das Markdown Badge (jetzt korrekt verpackt für Python)
st.markdown("[![No Backend](https://img.shields.io/badge/Architecture-100%25%20Lokal-success)](#)")

st.title("Willkommen in der PM AI Brain Pro Suite 🚀")
st.markdown("---")

st.markdown("""
Dieses Portal vereint alle datenschutzkonformen (Offline-)KI-Werkzeuge für dein Produktmanagement und RevOps-Team.

👈 **Wähle links im Menü dein Werkzeug aus:**

*   **🕵️‍♂️ PM Problem Copilot:** Wirf deine Support-Tickets und Umfragen hinein und chatte mit deinen Daten, um strategische Epics und Pain-Points zu extrahieren.
*   **💼 Sales Strategy Brain:** Lade Vertriebstransaktionen hoch und lass Python deterministisch deine ICP-Kandidaten (Ideal Customer Profile) berechnen.

*Hinweis: Dies ist eine 100% lokale Instanz. Es werden keine Daten an Cloud-Anbieter (LLM-APIs) gesendet.*
""")