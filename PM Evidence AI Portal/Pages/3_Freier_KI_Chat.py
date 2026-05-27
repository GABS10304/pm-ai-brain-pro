import streamlit as st
import pandas as pd
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI # NEU: Für IONOS
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# ==========================================
# 1. SETUP & PAGE CONFIG
# ==========================================
st.set_page_config(page_title="PM AI Brain Pro", layout="wide")
st.title("🧠 PM AI Brain Pro (RAG Edition)")

# 🚨 DEIN GEHEIMER IONOS-SCHLÜSSEL
# Kopiere deinen langen, echten Token exakt in diese Anführungszeichen:
IONOS_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiI0ZmIxYmQ1Ny1kZTE0LTRjY2QtOGRhNC03ZDNkODkzMGNjMTEiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJDb25Tb2wgQ29uc3VsdGluZyAmIFNvbHV0aW9ucyBTb2Z0d2FyZSBHbWJIIiwiaWF0IjoxNzc5MTk4NTI1LCJjbGllbnQiOiJVU0VSIiwiaWRlbnRpdHkiOnsiaXNQYXJlbnQiOmZhbHNlLCJjb250cmFjdE51bWJlciI6MzI0OTIzNDAsInJvbGUiOiJ1c2VyIiwicmVnRG9tYWluIjoiaW9ub3MuZGUiLCJyZXNlbGxlcklkIjo5MzM3NzIwNiwidXVpZCI6IjE2YzU2MGNkLWEyNjctNDlhYi04ZDUyLWVjOGE0ZTJkMzI4ZiIsInByaXZpbGVnZXMiOlsiQUNDRVNTX0FORF9NQU5BR0VfQUlfTU9ERUxfSFVCIl19LCJleHAiOjE4MTA3MzQ1MjV9.TBp-2dwuNu_-uNtiURWdMesdsNeinQrNgoiQj962qUvPuY2wVQEw069NSd3kit6Jz2RAyUX2kexCMWs3QQgyFPLDVdk0dp5MXigyJgCjbdv8OF2Y0Ev-th7GaAoICfpR--Bp9JmFNBzymz9Mbnl_TbDUdGHrAlfeZHH0U_suHkfenHpt0TebC0V-i7tG0sb9TbRuZM4TuQkBHWjb9OZpuVDQjOffQ9eb5x-LGr0ym0qF0QtFtRgHwE34lk1u6DXEi1q3S4tHBLpQh-JGWveyBsr4MaVaszb_AoaWDF1ol7diwTfQBrmwJhP-jvD2KCdVRcYHNNRJW0U2peAdRgXbCg" 

embeddings = OllamaEmbeddings(model="nomic-embed-text")
_SYSTEM_PROMPT = """Du bist Senior Product Manager. Deine Antworten basieren AUSSCHLIESSLICH auf dem Kontext, den das System dir mit der Frage liefert. Erfinde absolut nichts. Halte dich exakt an die Vorgaben des Nutzers."""

# Das Menü an der Seite (Jetzt inkl. IONOS!)
_MODEL_OPTIONS = {
    "☁️ IONOS Enterprise (120B Modell - Ultraschnell & DSGVO-konform)": "ionos",
    "💻 LOKAL: qwen3.5:9b (Analyst - Langsam, Offline)": "qwen3.5:9b",
    "💻 LOKAL: phi3 (Junior - Sehr schnell, Offline)": "phi3",
}

_RAG_SCORE_THRESHOLD: float = 0.42
_RAG_FETCH_K: int = 28  
_RAG_CONTEXT_CAP: int = 12  

if "messages" not in st.session_state:
    st.session_state.messages = [SystemMessage(content=_SYSTEM_PROMPT)]
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "csv_uploader_nonce" not in st.session_state:
    st.session_state.csv_uploader_nonce = 0

# ==========================================
# 2. SEITENLEISTE: DATEN-UPLOAD
# ==========================================
with st.sidebar:
    st.header("📂 Daten füttern")

    uploaded_files = st.file_uploader(
        "Lade PM-Backlog CSVs hoch",
        type=['csv'],
        accept_multiple_files=True,
        key=f"pm_csv_uploader_{st.session_state.csv_uploader_nonce}",
    )
    
    # Hier wählt der PM den Motor aus!
    selected_model_label = st.selectbox(
        "Wähle deinen KI-Motor",
        options=list(_MODEL_OPTIONS.keys()),
        index=0,
    )
    
    # Interne Speicherung der KI-Wahl
    aktuelle_ki_wahl = _MODEL_OPTIONS[selected_model_label]

    if uploaded_files:
        try:
            all_dataframes = []
            file_names = []

            for file in uploaded_files:
                df_temp = pd.read_csv(file, sep=";", encoding="utf-8-sig", on_bad_lines='skip')
                all_dataframes.append(df_temp)
                file_names.append(file.name)

            df_master = pd.concat(all_dataframes, ignore_index=True).fillna("")

            st.success(f"✅ {len(df_master)} Zeilen aus {len(file_names)} Dateien geladen!")
            st.markdown("### Aktive Akten:")
            for name in file_names:
                st.markdown(f"- 📄 `{name}`")
            st.markdown("---")

            if st.button("💾 Daten in Such-Index laden"):
                with st.spinner("Erstelle lokale Vektordatenbank..."):
                    docs = []
                    for index, row in df_master.iterrows():
                        text_content = f"Kunde/Modul: {row.get('Kunde', '')} {row.get('Ordner / Modul', '')} | Feedback: {row.get('Original-Wortlaut (Freitext)', str(row))}"
                        docs.append(Document(page_content=text_content, metadata={"zeile": str(index)}))
                    
                    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
                    st.session_state.vectorstore = vectorstore

                    bereit_nachricht = AIMessage(content="✅ Die Daten wurden lokal indexiert. Cloud- oder Offline-Wahl ist im Menü aktiv. Was möchtest du wissen?")
                    st.session_state.messages.append(bereit_nachricht)
                    st.rerun()

        except Exception as e:
            st.error(f"Fehler: {e}")
            
    if st.button("🧹 Session leeren", use_container_width=True):
        st.session_state.messages = [SystemMessage(content=_SYSTEM_PROMPT)]
        st.session_state.vectorstore = None
        st.session_state.csv_uploader_nonce += 1
        st.rerun()


# ==========================================
# 3. CHAT-INTERFACE & ENGINE-ROUTING
# ==========================================
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage) and "VERFÜGBARER KONTEXT:" not in msg.content:
        with st.chat_message("user"): st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"): st.write(msg.content)

user_input = st.chat_input("Fragen an deinen Daten-Ozean stellen...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    context_text = ""
    if st.session_state.vectorstore is not None:
        retriever = st.session_state.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "score_threshold": float(_RAG_SCORE_THRESHOLD),
                "k": _RAG_FETCH_K,
            },
        )
        relevante_zeilen = retriever.invoke(user_input)

        if not relevante_zeilen:
            st.warning("Keine relevanten Daten gefunden. Bitte umformulieren.")
            st.stop()

        relevante_zeilen = relevante_zeilen[: _RAG_CONTEXT_CAP]
        context_text = "\nVERFÜGBARER KONTEXT (Auszüge aus den Daten):\n"

        for i, doc in enumerate(relevante_zeilen):
            zeile = doc.metadata.get('zeile', 'Unbekannt')
            context_text += f"[Fundstelle {i+1} - Zeile {zeile}]: {doc.page_content}\n"
    else:
        context_text = "\n(HINWEIS: Index-Button wurde noch nicht geklickt).\n"

    hidden_prompt = f"{user_input}\n\n{context_text}"
    st.session_state.messages.append(HumanMessage(content=hidden_prompt))

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # DYNAMISCHER MOTOR-WECHSEL
        if aktuelle_ki_wahl == "ionos":
            # Wir feuern alles hoch in die Deutsche Cloud!
            llm = ChatOpenAI(
                api_key=IONOS_TOKEN,
                base_url="https://openai.inference.de-txl.ionos.com/v1",
                model="openai/gpt-oss-120b", 
                temperature=0.0
            )
        else:
            # Wir bleiben lokal und langsam auf dem Laptop
            llm = ChatOllama(
                model=aktuelle_ki_wahl,
                temperature=0.0,
                num_ctx=8192
            )

        # Die Antwort generieren lassen
        for chunk in llm.stream(st.session_state.messages):
            # Unterschiedliche APIs verarbeiten Chunks leicht anders
            if aktuelle_ki_wahl == "ionos":
                full_response += chunk.content
            else:
                full_response += chunk.content
                
            response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)
        st.session_state.messages.append(AIMessage(content=full_response))