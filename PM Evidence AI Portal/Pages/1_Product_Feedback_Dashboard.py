import streamlit as st
import pandas as pd
from google.cloud import bigquery
import os
import plotly.express as px
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# ==========================================
# 1. SETUP & AUTHENTIFIKATION
# ==========================================
st.set_page_config(page_title="PM Feedback Dashboard", page_icon="📊", layout="wide")
st.title("📊 Product Feedback (Live aus BigQuery)")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
key_path = os.path.join(BASE_DIR, "gcp-key.json")
report_path = os.path.join(BASE_DIR, "Finaler_PM_Report.md")

if not os.path.exists(key_path):
    st.error(f"Schlüssel nicht gefunden unter: {key_path}")
    st.stop()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

if "dash_messages" not in st.session_state:
    st.session_state.dash_messages = []

# ==========================================
# 2. NEU: DER DATENQUIELLEN-SCHALTER
# ==========================================
st.markdown("### 🎛️ Datenquelle wählen")
datenquelle = st.radio(
    "Welche Metrik möchtest du auswerten?",
    options=["🔧 Support-Tickets (HTML-Inbox)", "📋 Kundenumfragen (NPS / CSV)"],
    horizontal=True
)

# Wir weisen dem Radio-Button die korrekte BigQuery Tabelle zu
if "Support-Tickets" in datenquelle:
    aktuelle_tabelle = "pm-analytics-496606.pm_daten.html_tickets_rohdaten"
else:
    # Die Tabelle, die wir vorhin als Test-CSV/Umfrage hochgeladen hatten
    aktuelle_tabelle = "pm-analytics-496606.pm_daten.anonymes_pm_backlog"

# ==========================================
# 3. SQL ABFRAGE
# ==========================================
# Wir geben den Tabellennamen mit, damit Streamlit den Cache für beide Tabellen sauber trennt
@st.cache_data(ttl=600) 
def load_bigquery_data(table_name):
    client = bigquery.Client()
    query = f"""
        SELECT Ordner___Modul as Modul, COUNT(*) as Anzahl
        FROM `{table_name}`
        GROUP BY Ordner___Modul
        ORDER BY Anzahl DESC
    """
    query_job = client.query(query)
    return pd.DataFrame([dict(row) for row in query_job])

# ==========================================
# 4. DAS FRONTEND-LAYOUT
# ==========================================
try:
    with st.spinner(f"Lade Live-Daten aus {aktuelle_tabelle}..."):
        df = load_bigquery_data(aktuelle_tabelle)

    # --- TEIL 1: CHARTS ---
    st.subheader(f"Verteilung der Schmerzpunkte ({datenquelle})")
    fig = px.bar(df, x="Modul", y="Anzahl", text="Anzahl", color="Modul", template="plotly_white")
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- TEIL 2: DER KI-REPORT ---
    st.subheader("💡 Strategische KI-Analyse")
    ai_report_content = "Kein Report gefunden."
    
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8-sig") as f:
            ai_report_content = f.read()
            st.markdown(ai_report_content)
    else:
        st.warning("Bitte führe 'batch_aggregator.py' aus, um den Report zu generieren.")

    st.divider()

    # --- TEIL 3: DER SQL-DRILL-DOWN ---
    st.subheader("🔍 Deep-Dive: Rohdaten-Verifizierung")
    alle_module = df["Modul"].tolist()
    gewaehltes_modul = st.selectbox("Modul auswählen:", options=alle_module)

    if gewaehltes_modul:
        client = bigquery.Client()
        safe_modul = gewaehltes_modul.replace("\\", "\\\\")
        
        # Nutzt jetzt auch den dynamischen Tabellennamen!
        detail_query = f"""
            SELECT Quelle_Dateiname as Ticket_ID, Original_Wortlaut_Freitext as Problem_Beschreibung
            FROM `{aktuelle_tabelle}`
            WHERE Ordner___Modul = '{safe_modul}'
        """
        detail_df = pd.DataFrame([dict(row) for row in client.query(detail_query)])
        st.dataframe(detail_df, hide_index=True, use_container_width=True)

    st.divider()

    # --- TEIL 4: INTERAKTION MIT DEM REPORT ---
    st.subheader("💬 Q&A zum Report")
    
    if len(st.session_state.dash_messages) == 0:
        st.session_state.dash_messages.append(SystemMessage(content=f"Du bist Produktmanager. Beantworte alle Fragen AUSSCHLIESSLICH basierend auf diesem Report: \n{ai_report_content}"))

    for msg in st.session_state.dash_messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"): st.write(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"): st.write(msg.content)

    if user_input := st.chat_input("Beispiel: Schreibe mir für Epic 2 ein fertiges Jira Ticket..."):
        with st.chat_message("user"): st.write(user_input)
        st.session_state.dash_messages.append(HumanMessage(content=user_input))
        
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            llm = ChatOllama(model="qwen3.5:9b", temperature=0.0)
            
            for chunk in llm.stream(st.session_state.dash_messages):
                full_response += chunk.content
                response_placeholder.markdown(full_response + "▌")
                
            response_placeholder.markdown(full_response)
            st.session_state.dash_messages.append(AIMessage(content=full_response))

except Exception as e:
    st.error(f"Es gab ein Problem: {e}")