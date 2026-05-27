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
# 2. DER DATENQUELLEN-SCHALTER
# ==========================================
st.markdown("### 🎛️ Datenquelle wählen")
datenquelle = st.radio(
    "Welche Metrik möchtest du auswerten?",
    options=["🔧 Support-Tickets (HTML-Inbox)", "📋 Kundenumfragen (NPS / CSV)"],
    horizontal=True
)

if "Support-Tickets" in datenquelle:
    aktuelle_tabelle = "pm-analytics-496606.pm_daten.html_tickets_rohdaten"
    gruppierungs_spalte = "Ordner___Modul"
    ui_name = "Modul"
else:
    aktuelle_tabelle = "pm-analytics-496606.pm_daten.anonymes_pm_backlog"
    gruppierungs_spalte = "Kunde" 
    ui_name = "Kunde / Ort"

# ==========================================
# 3. DYNAMISCHE SQL ABFRAGE
# ==========================================
@st.cache_data(ttl=600) 
def load_bigquery_data(table_name, group_col, label):
    client = bigquery.Client()
    # Benennt die Spalte SQL-intern jetzt dynamisch absolut korrekt!
    safe_label = label.replace(' / ', '_')
    query = f"""
        SELECT {group_col} as {safe_label}, COUNT(*) as Anzahl
        FROM `{table_name}`
        GROUP BY {group_col}
        ORDER BY Anzahl DESC
    """
    query_job = client.query(query)
    return pd.DataFrame([dict(row) for row in query_job])

# ==========================================
# 4. DAS FRONTEND-LAYOUT
# ==========================================
try:
    with st.spinner(f"Lade Live-Daten aus {aktuelle_tabelle}..."):
        df = load_bigquery_data(aktuelle_tabelle, gruppierungs_spalte, ui_name)
        safe_col_name = ui_name.replace(' / ', '_')

    # --- TEIL 1: CHARTS ---
    st.subheader(f"Verteilung der Schmerzpunkte ({datenquelle[:15]}...)")
    fig = px.bar(df, x=safe_col_name, y="Anzahl", text="Anzahl", color=safe_col_name, template="plotly_white")
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
    alle_kategorien = df[safe_col_name].tolist()
    gewaehltes_item = st.selectbox(f"{ui_name} auswählen:", options=alle_kategorien)

    if gewaehltes_item:
        client = bigquery.Client()
        safe_item = gewaehltes_item.replace("\\", "\\\\")
        
        detail_query = f"""
            SELECT *
            FROM `{aktuelle_tabelle}`
            WHERE {gruppierungs_spalte} = '{safe_item}'
        """
        detail_df = pd.DataFrame([dict(row) for row in client.query(detail_query)])
        
        cols_to_show = [c for c in detail_df.columns if c not in ["Kategorie", "Ordner___Modul"]]
        st.dataframe(detail_df[cols_to_show], hide_index=True, use_container_width=True)

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
    st.error(f"Es gab ein Problem bei der Auswertung (SQL): {e}")