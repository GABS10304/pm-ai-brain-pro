import pandas as pd
import numpy as np
import os

# ==========================================
# 1. SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "Rohe_Sales_Daten.xlsx") # Oder .csv
OUTPUT_FILE = os.path.join(BASE_DIR, "Sales_ICP_Strategie_Daten.csv")

def finde_spalte(spalten_liste, suchbegriffe):
    for spalte in spalten_liste:
        for begriff in suchbegriffe:
            if begriff in spalte:
                return spalte
    return None

def process_sales_data():
    print("🚀 Starte RevOps Daten-Pumpe & ICP-Scoring...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"⚠️ Fehler: Datei {INPUT_FILE} nicht gefunden!")
        return

    # 1. DATEN CADEN (Nimmt das erste Blatt mit den Transaktionen)
    try:
        if INPUT_FILE.lower().endswith(".csv"):
            df = pd.read_csv(INPUT_FILE, sep=";", encoding="utf-8-sig", on_bad_lines='skip')
        else:
            df = pd.read_excel(INPUT_FILE, sheet_name=0)
            print("📚 Excel-Vertragsdaten erfolgreich gelesen!")
    except Exception as e:
        print(f"❌ Dateifehler beim Laden: {e}")
        return

    df.columns = df.columns.str.lower().str.strip()

    # 2. SPALTEN ZUWEISEN (Exakt angepasst auf dein Excel-Format)
    # Bevorzugt exakt "kunde", falls es auch "kundennr." gibt
    if "kunde" in df.columns:
        kd_col = "kunde"
    else:
        kd_col = finde_spalte(df.columns, ["name", "kunde"])
        
    umsatz_col = finde_spalte(df.columns, ["gesamt", "umsatz"]) 
    rabatt_col = finde_spalte(df.columns, ["prozent", "rabatt"]) 
    artikel_col = finde_spalte(df.columns, ["artikelgruppe", "artikelbezeichnung"]) 

    if not all([kd_col, umsatz_col, rabatt_col, artikel_col]):
        print(f"🛑 Abbruch: Konnte nicht alle Kernspalten finden!")
        return

    print(f"📊 {len(df)} Vertragszeilen geladen. Analysiere Kundenstrukturen...")

    # =========================================================
    # 3. KUNDENTYP-EXTRAKTION (Der schlaue Text-Scanner)
    # =========================================================
    df[kd_col] = df[kd_col].fillna("Unbekannt").astype(str)
    
    def extrahiere_kundentyp(name):
        name_lower = name.lower()
        org_formen = {
            'bistum': 'Bistum / Kirche', 'diözese': 'Bistum / Kirche', 'pfarrei': 'Bistum / Kirche',
            'zweckverband': 'Zweckverband', 'wasserverband': 'Zweckverband', 'zwa': 'Zweckverband',
            'gmbh': 'Privatwirtschaft (Firma)', ' ag ': 'Privatwirtschaft (Firma)', '& co': 'Privatwirtschaft (Firma)',
            'verwaltungsgemeinschaft': 'Verwaltungsgemeinschaft (VG)', 'vg ': 'Verwaltungsgemeinschaft (VG)',
            'landratsamt': 'Landkreis (LRA)', 'landkreis': 'Landkreis (LRA)',
            'stadt': 'Stadt',
            'markt ': 'Marktgemeinde', 'marktgemeinde': 'Marktgemeinde',
            'gemeinde': 'Gemeinde'
        }
        for schluesselwort, saubere_kategorie in org_formen.items():
            if schluesselwort in name_lower:
                return saubere_kategorie
        return 'Behörde/Orga (ohne Kürzel)'

    df['Kundentyp'] = df[kd_col].apply(extrahiere_kundentyp)
    
    # DSGVO-Maßnahme: Klarnamen-Spalte löschen
    df = df.drop(columns=[kd_col])

    # =========================================================
    # 4. ZAHLEN BEREINIGEN
    # =========================================================
    df[umsatz_col] = pd.to_numeric(df[umsatz_col].astype(str).str.replace(',', '.'), errors="coerce").fillna(0)
    df[rabatt_col] = pd.to_numeric(df[rabatt_col].astype(str).str.replace(',', '.'), errors="coerce").fillna(0)
    df["rabatt_echt"] = np.where(df[rabatt_col] <= 1, df[rabatt_col] * 100, df[rabatt_col])

    # =========================================================
    # 5. ICP AGGREGATION
    # ==========================================
    print("🧠 Berechne Ideal Customer Profiles (ICP)...")
    
    aggregation = {
        umsatz_col: "sum",           
        "rabatt_echt": "mean",       
        "art.nr.": "nunique" # Trick: Zählt die Zeilen, da Kunden-Spalte gelöscht ist
    }
    
    # Fallback, falls 'art.nr.' so nicht heißt
    zähl_spalte = finde_spalte(df.columns, ["art.nr", "pos", "vertrags"])
    if zähl_spalte:
        aggregation = {umsatz_col: "sum", "rabatt_echt": "mean", zähl_spalte: "count"}
    
    df_grouped = df.groupby(['Kundentyp', artikel_col]).agg(aggregation).reset_index()

    df_grouped.rename(columns={
        umsatz_col: "Gesamt_Netto_Volumen",
        "rabatt_echt": "Ø_Rabatt_Prozent",
        zähl_spalte if zähl_spalte else "art.nr.": "Anzahl_Vertragspositionen"
    }, inplace=True)

    # =========================================================
    # 6. ICP SCORE
    # =========================================================
    max_umsatz = df_grouped["Gesamt_Netto_Volumen"].max() if df_grouped["Gesamt_Netto_Volumen"].max() > 0 else 1
    max_kunden = df_grouped["Anzahl_Vertragspositionen"].max() if df_grouped["Anzahl_Vertragspositionen"].max() > 0 else 1
    
    df_grouped["ICP_Score"] = (
        (df_grouped["Gesamt_Netto_Volumen"] / max_umsatz * 40) +    
        (df_grouped["Anzahl_Vertragspositionen"] / max_kunden * 40) + 
        ((100 - df_grouped["Ø_Rabatt_Prozent"]) / 100 * 20)           
    ).round(0)

    df_grouped = df_grouped.sort_values(by="ICP_Score", ascending=False)
    df_grouped["Gesamt_Netto_Volumen"] = df_grouped["Gesamt_Netto_Volumen"].round(2)
    df_grouped["Ø_Rabatt_Prozent"] = df_grouped["Ø_Rabatt_Prozent"].round(2)

    # 7. EXPORT
    df_grouped.to_csv(OUTPUT_FILE, sep=";", index=False, encoding="utf-8-sig")
    print(f"\n🎉 SAUBER: Klarnamen vernichtet! {len(df_grouped)} anonyme Strategie-Zeilen generiert.")
    print(f"Die Datei liegt als '{os.path.basename(OUTPUT_FILE)}' bereit!")

if __name__ == "__main__":
    process_sales_data()