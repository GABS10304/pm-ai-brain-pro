import streamlit as st
import pandas as pd
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# ==========================================
# 1. SETUP & PAGE CONFIG
# ==========================================
st.set_page_config(page_title="PM AI Brain Pro", layout="wide")
st.title("🧠 PM AI Brain Pro (RAG Edition)")

llm = ChatOllama(model="qwen3.5:9b", temperature=0.1, num_ctx=8192)
embeddings = OllamaEmbeddings(model="nomic-embed-text")

if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="""Du bist Senior Product Manager. Deine Antworten basieren AUSSCHLIESSLICH auf dem Kontext, den das System dir mit der Frage liefert. Erfinde absolut nichts. Halte dich exakt an die Vorgaben des Nutzers.""")
    ]
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

# ==========================================
# 2. SEITENLEISTE: DATEN-UPLOAD & INDEXIERUNG
# ==========================================
with st.sidebar:
    st.header("📂 Daten füttern (Multi-Upload)")
    
    uploaded_files = st.file_uploader("Lade PM-Backlog CSVs hoch", type=['csv'], accept_multiple_files=True)
    
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
                with st.spinner("Erstelle Vektordatenbank (Säubere und verkleinere Chunks)..."):
                    
                    docs = []
                    # HIER IST DER REPARIERTE BLOCK
                    for index, row in df_master.iterrows():
                        # Wir laden NUR noch den sauberen Kern-Inhalt, keinen nervigen Spalten-Müll mehr
                        text_content = f"Kunde/Modul: {row.get('Kunde', '')} {row.get('Ordner / Modul', '')} | Feedback: {row.get('Original-Wortlaut (Freitext)', str(row))}"
                        docs.append(Document(page_content=text_content, metadata={"zeile": str(index)}))

                    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
                    st.session_state.vectorstore = vectorstore
                    
                    bereit_nachricht = AIMessage(content="✅ Die Daten wurden erfolgreich indexiert und mein Speicher ist aktiv. Du kannst mir gezielte Fragen zu einzelnen Kunden oder Modulen stellen.")
                    st.session_state.messages.append(bereit_nachricht)
                    st.rerun()
                
        except Exception as e:
            st.error(f"Fehler: {e}")

# ==========================================
# 3. CHAT-INTERFACE
# ==========================================
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage) and "VERFÜGBARER KONTEXT:" not in msg.content:
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

user_input = st.chat_input("Fragen an deinen Daten-Ozean stellen...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    
    context_text = ""
    if st.session_state.vectorstore is not None:
        # HIER IST DAS ZWEITE UPDATE: Nur noch 15 Chunks statt 30, um den Puffer zu schützen
        retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 15})
        relevante_zeilen = retriever.invoke(user_input)
        
        context_text = "\nVERFÜGBARER KONTEXT (Auszüge aus den Daten):\n"
        for i, doc in enumerate(relevante_zeilen):
            context_text += f"[Fundstelle {i+1}]: {doc.page_content}\n"
    else:
        context_text = "\n(HINWEIS: Index-Button wurde noch nicht geklickt).\n"

    hidden_prompt = f"{user_input}\n\n{context_text}"
    st.session_state.messages.append(HumanMessage(content=hidden_prompt))
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        for chunk in llm.stream(st.session_state.messages):
            full_response += chunk.content
            response_placeholder.markdown(full_response + "▌")
            
        response_placeholder.markdown(full_response)
        st.session_state.messages.append(AIMessage(content=full_response))