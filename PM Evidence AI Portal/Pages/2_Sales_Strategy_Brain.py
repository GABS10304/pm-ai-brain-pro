import streamlit as st
import pandas as pd
import numpy as np
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# ==========================================
# 1. SETUP & KI KONFIGURATION
# ==========================================
st.set_page_config(page_title="Sales Strategy Brain", layout="wide")
st.title("💼 Sales Strategy Brain (ICP & RevOps)")

# Wir nutzen Qwen für brillante Strategietexte (Faktenbasiert: Temp 0.0)
llm = ChatOllama(model="qwen3.5:9b", temperature=0.0)

REQUIRED = [
    "Kundentyp", "Vertragsbeginn", "Abrechnungsart",
    "Artikelbezeichnung", "Menge", "Einzelpreis", "Rabatt Prozent"
]

# ==========================================
# 2. LAYER A: DATEN-PIPELINE (PYTHON RECHNET)
# ==========================================
@st.cache_data # Streamlit Cache, damit er bei UI-Klicks nicht neu rechnet!
def load_and_prepare_data(file) -> pd.DataFrame:
    # 1. Einlesen
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, sep=";") # Typisches deutsches Format
    else:
        df = pd.read_excel(file, engine="openpyxl")
        
    df.columns = [c.strip() for c in df.columns]
    
    # Spalten checken
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Fehlende Spalten: {missing}")

    # 2. Bereinigen
    df["Vertragsbeginn"] = pd.to_datetime(df["Vertragsbeginn"], errors="coerce")
    for c in ["Menge", "Einzelpreis", "Rabatt Prozent"]:
        df[c] = pd.to_numeric(str(df[c]).replace(',', '.'), errors="coerce") # Fängt deutsche Kommas sicher ab

    # 3. Rabatt normalisieren
    r = df["Rabatt Prozent"].fillna(0)
    df["Rabatt_Pct"] = np.where(r <= 1, r * 100, r)

    # 4. Netto berechnen (falls nicht da)
    if "Netto-Wert" not in df.columns:
        df["Netto_Wert"] = df["Menge"] * df["Einzelpreis"] * (1 - df["Rabatt_Pct"] / 100)
    else:
        df["Netto_Wert"] = pd.to_numeric(str(df["Netto-Wert"]).replace(',', '.'), errors="coerce")

    # 5. Anonymer Contract-Key
    df["contract_key"] = (
        df["Kundentyp"].astype(str) + "||" +
        df["Vertragsbeginn"].astype(str) + "||" +
        df["Abrechnungsart"].astype(str)
    )
    return df

@st.cache_data
def build_aggregations(df: pd.DataFrame):
    # Vertragsebene
    contract_cols = ["Kundentyp", "Vertragsbeginn", "Abrechnungsart", "contract_key"]
    contract = df.groupby(contract_cols, dropna=False).agg(
        Netto_Wert=("Netto_Wert", "sum"),
        Rabatt_Pct=("Rabatt_Pct", "mean"),
        Einzelpreis=("Einzelpreis", "mean"),
        Positionen=("Artikelbezeichnung", "size"),
    ).reset_index()

    # Tabelle 1: Segmentübersicht
    seg = contract.groupby("Kundentyp", dropna=False).agg(
        Anzahl_Vertraege=("contract_key", "nunique"),
        Ø_Netto=("Netto_Wert", "mean"),
        Ø_Rabatt_Prozent=("Rabatt_Pct", "mean"),
        Ø_Einzelpreis=("Einzelpreis", "mean"),
    ).reset_index()

    # Tabelle 3: Rabattmuster (vereinfacht für Streamlit)
    q25 = seg["Ø_Rabatt_Prozent"].quantile(0.25)
    q75 = seg["Ø_Rabatt_Prozent"].quantile(0.75)
    
    def interp(x):
        if x <= q25: return "stark (niedriger Rabatt)"
        if x >= q75: return "schwach (hoher Rabatt)"
        return "mittel"
    
    seg["Preisdisziplin"] = seg["Ø_Rabatt_Prozent"].apply(interp)
    
    return contract, seg

# ==========================================
# 3. LAYER B: UI EXPORT (STREAMLIT RENDERING)
# ==========================================
with st.sidebar:
    st.header("📂 Sales-Daten Upload")
    st.info("Daten müssen die 7 definierten Spalten enthalten (keine Einzelkundendaten nötig).")
    uploaded_file = st.file_uploader("Lade CSV oder Excel hoch", type=["csv", "xlsx"])

if uploaded_file:
    try:
        with st.spinner("Berechne Contract-Keys und aggregiere Zahlen..."):
            df_raw = load_and_prepare_data(uploaded_file)
            df_contract, df_segment = build_aggregations(df_raw)
            
        st.success("✅ Daten erfolgreich deterministisch aggregiert (Ohne KI-Halluzination).")
        
        # Rendern als st.dataframe (Sortierbar, scrollbar)
        st.subheader("📊 1. Segmentübersicht & Rabattmuster")
        st.dataframe(df_segment, use_container_width=True)
        
        st.divider()
        
        # ==========================================
        # 4. LAYER C: KI STRATEGIE-TEXTER
        # ==========================================
        st.subheader("🤖 KI Sales Strategist (Cheat Sheet)")
        
        if st.button("Erstelle ICP-Kandidaten & Sales Cheat Sheet"):
            # Wandle aggregierte DF in Text um (Niemals Rohdaten!)
            daten_fuer_ki = f"SEGMENTÜBERSICHT:\n{df_segment.to_markdown(index=False)}"
            
            prompt = f"""Du bist ein präziser Data Analyst und Sales Strategist.
            Du erhältst ausschließlich aggregierte Tabellen (keine Rohdaten, keine Einzelkunden).
            Du darfst nur Aussagen ableiten, die in den Tabellen enthalten sind.
            Keine Annahmen, keine Schätzungen.
            
            INPUT:
            {daten_fuer_ki}
            
            AUFGABE:
            Erstelle basierend darauf:
            
            ### 5. ICP-/Sales-Kandidaten
            Identifiziere die 2 bis 3 lukrativsten Kundentypen (Segmente) aus der Tabelle. Nenne:
            - Den Kundentyp
            - Eine analytische Begründung (z.B. hohes Netto bei starker Preisdisziplin)
            - Die Vertriebspriorität (1, 2 oder 3)
            
            ### 6. Sales Cheat Sheet
            5 bis 8 Bullet Points für das Vertriebsteam:
            - Auf welche Segmente fokussieren?
            - Wo muss die Rabattdisziplin verbessert werden?
            - Defensive vs. Offensive Strategie basierend auf den Daten.
            
            Stil: analytisch, präzise, nüchtern, strategisch. Kein Marketing-Gerede.
            """
            
            with st.spinner("KI Analyst wertet Segment-Daten aus..."):
                # System Message und Human Message kombinieren
                messages = [
                    SystemMessage(content="Du bist ein analytischer Data Scientist. Du lieferst nur knallharte Fakten."),
                    HumanMessage(content=prompt)
                ]
                
                # Streaming Output Container
                response_container = st.empty()
                full_text = ""
                
                # KI Stream starten
                for chunk in llm.stream(messages):
                    full_text += chunk.content
                    response_container.markdown(full_text + "▌")
                
                # Fertigen Text anzeigen
                response_container.markdown(full_text)

    except Exception as e:
        st.error(f"Fehler in der Daten-Pipeline: {e}")