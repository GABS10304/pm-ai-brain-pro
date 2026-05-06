import streamlit as st
import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# ==========================================
# 1. SETUP & PAGE CONFIG
# ==========================================
st.set_page_config(page_title="Product Discovery", layout="wide")
st.title("💡Problem-Space Copilot")

# Lokales Modell auf Qwen und strikte Fakten (Temperature 0.0) gestellt
llm = ChatOllama(model="qwen3.5:9b", temperature=0.0)

# Chat-Historie initiieren
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="""Du bist ein Senior Product Manager für B2B-Software. 
        DEIN FOKUS LIEGT ZU 100% IM PROBLEM SPACE. 
        Du suchst nach Pain Points, Needs und Workarounds. 
        REGELN:
        1. Erfinde NIEMALS Features, Lösungen, Nutzer oder Zitate. 
        2. Halte dich EXAKT an die Fakten, die dir hochgeladen werden.
        3. Wenn es keine Daten zu einer Frage gibt, antworte zwingend mit: 'Dazu liegen mir keine Daten vor.'""")
    ]
if "dataset" not in st.session_state:
    st.session_state.dataset = None

# ==========================================
# 2. SEITENLEISTE: DATEN-UPLOAD
# ==========================================
with st.sidebar:
    st.header("📂 Daten füttern")
    uploaded_file = st.file_uploader("Lade deine PM-Backlog CSV hoch", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Datei einlesen
            df = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig")
            st.session_state.dataset = df
            st.success(f"{len(df)} Zeilen erfolgreich geladen!")
            
            # Button, um die kompletten Daten einzuimpfen
            if st.button("KI die kompletten Daten übergeben"):
                
                # Tabelle in Text umwandeln (max 500 Zeilen aus Performance-Gründen)
                data_string = df.head(500).to_markdown(index=False)
                
                prompt = f"""Ich habe dir hier unseren echten B2B Datensatz hochgeladen ({len(df)} Zeilen).
                Lies dir diese Daten durch und nutze für alle weiteren Antworten AUSSCHLIESSLICH diese Daten:
                
                DATENSATZ:
                {data_string}
                
                Bitte bestätige mir ganz kurz (1 Satz), dass du die Fakten verstanden hast und bereit bist für meine Fragen."""
                
                st.session_state.messages.append(HumanMessage(content=prompt))
                with st.spinner("KI verarbeitet und indexiert den gesamten Datensatz..."):
                    response = llm.invoke(st.session_state.messages)
                    st.session_state.messages.append(AIMessage(content=response.content))
                st.rerun()
                
        except Exception as e:
            st.error(f"Fehler beim Lesen der CSV: {e}")

# ==========================================
# 3. CHAT-INTERFACE
# ==========================================
# Zeige alle bisherigen Nachrichten
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage) and "DATENSATZ:" not in msg.content:
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

# Nutzereingabe
user_input = st.chat_input("Beispiel: Gibt es Feedback aus Otterfing? oder Was ist der größte Schmerzpunkt?")

if user_input:
    # Zeige Nutzerfrage
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append(HumanMessage(content=user_input))
    
    # KI Antwort aufbauen und streamen
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in llm.stream(st.session_state.messages):
            full_response += chunk.content
            response_placeholder.markdown(full_response + "▌")
            
        response_placeholder.markdown(full_response)
        st.session_state.messages.append(AIMessage(content=full_response))