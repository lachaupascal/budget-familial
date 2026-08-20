import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, date
import io
from fpdf import FPDF

# --- 1. CONFIGURATION DE LA PAGE (UNE SEULE FOIS AU TOUT DÉBUT) ---
st.set_page_config(page_title="Budget Familial", layout="wide", page_icon="💰")

# --- 2. SÉCURITÉ & AUTHENTIFICATION ---
USERS = {
    "pascalL": "14juin2008AUREC@",
    "manueQL": "manue4sousAUREC@"
}

if "est_connecte" not in st.session_state:
    st.session_state["est_connecte"] = False

if not st.session_state["est_connecte"]:
    st.title("🔒 Connexion requise")
    
    with st.form(key="form_connexion"):
        user = st.text_input("Identifiant")
        pwd = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
        
        if submit:
            if user in USERS and USERS[user] == pwd:
                st.session_state["est_connecte"] = True
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
    
    # Arrête impérativement l'exécution si non connecté
    st.stop()

# --- BARRE LATÉRALE DE DÉCONNEXION ---
if st.sidebar.button("🚪 Se déconnecter"):
    st.session_state["est_connecte"] = False
    st.rerun()

# --- 3. APPLICATION BUDGET FAMILIAL ---
DB_FILE = "budget_data.db"

CATEGORIES = [
    "Revenus",
    "Frais Fixes - Crédits",
    "Frais Fixes - Assurances",
    "Frais Fixes - Impôts",
    "Frais Fixes - Téléphones & Net",
    "Frais Fixes - Garde & Écoles",
    "Frais Fixes - Banques & Divers",
    "Courses",
    "Essence",
    "Maison / Bricolage",
    "Restaurant",
    "Beauté & Vêtements",
    "Loisirs & Sorties",
    "Santé & Mutuelle",
    "Épargne & Placements",
    "Autre dépense"
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            categorie TEXT,
            type TEXT,
            libelle TEXT,
            sorties REAL,
            entrees REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            annee_mois TEXT PRIMARY KEY,
            montant REAL
        )
    ''')
    
    c.execute("INSERT OR IGNORE INTO reports (annee_mois, montant) VALUES ('2026-07', -1224.20)")

    c.execute("SELECT COUNT(*) FROM operations")
    if c.fetchone()[0] == 0:
        initial_data = [
            ("2026-08-01", "Revenus", "Virement", "Salaire 1", 0.0, 3226.31),
            ("2026-08-01", "Revenus", "Virement", "Salaire 2", 0.0, 2577.0),
            ("2026-08-01", "Revenus", "Virement", "CAF", 0.0, 170.21),
            ("2026-08-01", "Frais Fixes - Assurances", "Virement", "Assurance Macif", 12.52, 0.0),
            ("2026-08-01", "Frais Fixes - Assurances", "Virement", "Assurance Habitation / Auto", 134.34, 0.0),
            ("2026-08-01", "Frais Fixes - Assurances", "Virement", "Assurance Pret", 14.04, 0.0),
            ("2026-08-01", "Frais Fixes - Assurances", "Virement", "MACIF Assurance", 30.0, 0.0),
            ("2026-08-01", "Frais Fixes - Assurances", "Prélèvement", "Allianz Assurances", 22.18, 0.0),
            ("2026-08-01", "Frais Fixes - Téléphones & Net", "Virement", "SFR Internet", 22.39, 0.0),
            ("2026-08-01", "Frais Fixes - Téléphones & Net", "Virement", "Internet FREE", 50.0, 0.0),
            ("2026-08-01", "Frais Fixes - Téléphones & Net", "Virement", "Free Mobile", 4.0, 0.0),
            ("2026-08-01", "Frais Fixes - Impôts", "Virement", "Impôt Revenu", 432.0, 0.0),
            ("2026-08-01", "Frais Fixes - Impôts", "Virement", "Impôts Foncier", 13.0, 0.0),
            ("2026-08-01", "Frais Fixes - Crédits", "Virement", "Crédit Mutuel", 419.41, 0.0),
            ("2026-08-01", "Frais Fixes - Crédits", "Virement", "Crédit Voiture", 300.0, 0.0),
            ("2026-08-01", "Frais Fixes - Crédits", "Virement", "Crédit Location WGA", 262.44, 0.0),
            ("2026-08-01", "Frais Fixes - Garde & Écoles", "Virement", "Frais Garde / Nounou", 282.80, 0.0),
            ("2026-08-01", "Frais Fixes - Garde & Écoles", "Virement", "École / Cantine", 2.0, 0.0),
            ("2026-08-01", "Frais Fixes - Banques & Divers", "Virement", "Frais Banque", 120.36, 0.0),
            ("2026-08-02", "Courses", "CB", "Courses Carrefour", 85.30, 0.0),
            ("2026-08-03", "Essence", "CB", "Essence Intermarché", 58.72, 0.0),
            ("2026-08-04", "Santé & Mutuelle", "CB", "Pharmacie", 18.41, 0.0),
            ("2026-08-05", "Restaurant", "CB", "Restaurant / Cafétéria", 43.50, 0.0),
            ("2026-08-08", "Maison / Bricolage", "CB", "Bricolage Leroy Merlin", 110.43, 0.0),
            ("2026-08-10", "Courses", "CB", "Courses Lidl", 62.15, 0.0),
            ("2026-08-12", "Essence", "CB", "Plein Essence Total", 71.00, 0.0),
            ("2026-08-14", "Beauté & Vêtements", "CB", "Achat Vêtements", 49.90, 0.0),
            ("2026-08-15", "Épargne & Placements", "Virement", "Virement Épargne", 200.0, 0.0)
        ]
        c.executemany('''
            INSERT INTO operations (date, categorie, type, libelle, sorties, entrees)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', initial_data)
        conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM operations", conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def get_report(annee_mois):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT montant FROM reports WHERE annee_mois = ?", (annee_mois,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0.0

def set_report(annee_mois, montant):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO reports (annee_mois, montant) VALUES (?, ?)", (annee_mois, montant))
    conn.commit()
    conn.close()

def add_operation(op_date, op_cat, op_type, op_libelle, op_sorties, op_entrees):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO operations (date, categorie, type, libelle, sorties, entrees)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (op_date.strftime("%Y-%m-%d"), op_cat, op_type, op_libelle, op_sorties, op_entrees))
    conn.commit()
    conn.close()

def delete_operation(op_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM operations WHERE id = ?", (op_id,))
    conn.commit()
    conn.close()

def generate_pdf(df_m, period_str, tot_e, tot_s, report, solde_m, solde_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Rapport Budget - {period_str}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Total Entrees: {tot_e:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Total Depenses: {tot_s:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Solde du Mois: {solde_m:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Report Mois Precedent: {report:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Solde Final Compte: {solde_f:.2f} EUR", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(25, 7, "Date", 1)
    pdf.cell(45, 7, "Categorie", 1)
    pdf.cell(60, 7, "Libelle", 1)
    pdf.cell(30, 7, "Sorties (EUR)", 1)
    pdf.cell(30, 7, "Entrees (EUR)", 1)
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df_m.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        cat_str = str(row['categorie'])[:22]
        lib_str = str(row['libelle'])[:30]
        pdf.cell(25, 6, date_str, 1)
        pdf.cell(45, 6, cat_str, 1)
        pdf.cell(60, 6, lib_str, 1)
        pdf.cell(30, 6, f"{row['sorties']:.2f}", 1)
        pdf.cell(30, 6, f"{row['entrees']:.2f}", 1)
        pdf.ln()
        
    return bytes(pdf.output())

init_db()

st.title("💰 Budget Familial - Suivi & Bilan")

st.sidebar.header("➕ Saisir une dépense / entrée")
with st.sidebar.form("form_op", clear_on_submit=True):
    op_date = st.date_input("Date", date(2026, 8, 20))
    op_type = st.selectbox("Moyen", ["CB", "Virement", "Prélèvement", "Espèces"])
    op_cat = st.selectbox("Catégorie", CATEGORIES)
    op_libelle = st.text_input("Libellé / Commentaire")
    op_montant = st.number_input("Montant (€)", min_value=0.0, step=5.0, format="%.2f")
    op_sens = st.radio("Type", ["Dépense (Sortie)", "Revenu (Entrée)"])
    
    if st.form_submit_button("💾 Enregistrer"):
        sorties = op_montant if op_sens == "Dépense (Sortie)" else 0.0
        entrees = op_montant if op_sens == "Revenu (Entrée)" else 0.0
        add_operation(op_date, op_cat, op_type, op_libelle, sorties, entrees)
        st.sidebar.success("Enregistré avec succès !")
        st.rerun()

df = load_data()

tab1, tab2, tab3 = st.tabs(["📊 Suivi Mensuel", "📅 Bilan Annuel", "📝 Historique & Reports"])

with tab1:
    if not df.empty:
        df['Annee'] = df['date'].dt.year
        df['Mois_Num'] = df['date'].dt.month
        df['Mois_Str'] = df['date'].dt.strftime('%m - %B')
        
        c_annee, c_mois = st.columns(2)
        with c_annee:
            annee_sel = st.selectbox("Année", sorted(df['Annee'].unique(), reverse=True))
        with c_mois:
            df_a = df[df['Annee'] == annee_sel]
            mois_sel = st.selectbox("Mois", sorted(df_a['Mois_Str'].unique()))

        df_m = df[(df['Annee'] == annee_sel) & (df['Mois_Str'] == mois_sel)]
        
        cur_month_num = df_m['Mois_Num'].iloc[0] if not df_m.empty else 8
        prev_year = annee_sel - 1 if cur_month_num == 1 else annee_sel
        prev_month_num = 12 if cur_month_num == 1 else cur_month_num - 1
        prev_annee_mois = f"{prev_year}-{prev_month_num:02d}"
        
        report_n_1 = get_report(prev_annee_mois)

        tot_entrees = df_m["entrees"].sum()
        tot_sorties = df_m["sorties"].sum()
        solde_mois = tot_entrees - tot_sorties
        solde_final = solde_mois + report_n_1

        df_ff = df_m[df_m['categorie'].str.startswith("Frais Fixes")]
        tot_frais_fixes = df_ff["sorties"].sum()

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Revenus Total", f"{tot_entrees:.2f} €")
        k2.metric("Frais Fixes", f"{tot_frais_fixes:.2f} €")
        k3.metric("Solde Mois", f"{solde_mois:.2f} €")
        
        col_rep = "#1E88E5" if report_n_1 >= 0 else "#E53935"
        k4.markdown(f'<div style="background-color: #f9f9f9; padding: 8px; border-radius: 8px; border: 1px solid #e0e0e0; text-align:center;"><p style="margin:0; font-size: 11px; color: #555;">Report Mois N-1 ({prev_annee_mois})</p><p style="margin:0; font-size: 18px; font-weight: bold; color: {col_rep};">{report_n_1:.2f} €</p></div>', unsafe_allow_html=True)

        col_final = "#1E88E5" if solde_final >= 0 else "#E53935"
        k5.markdown(f'<div style="background-color: #f9f9f9; padding: 8px; border-radius: 8px; border: 1px solid #1e88e5; text-align:center;"><p style="margin:0; font-size: 18px; font-weight: bold; color: {col_final};">{solde_final:.2f} €</p></div>', unsafe_allow_html=True)

        st.divider()

        # EXPORTS EXCEL & PDF
        st.subheader("📥 Exporter le bilan du mois")
        exp_col1, exp_col2 = st.columns(2)
        
        with exp_col1:
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_export = df_m[['date', 'categorie', 'type', 'libelle', 'sorties', 'entrees']].copy()
                df_export['date'] = df_export['date'].dt.strftime('%Y-%m-%d')
                df_export.to_excel(writer, index=False, sheet_name=f"Budget_{mois_sel[:2]}")
            st.download_button(
                label="📊 Télécharger la feuille Excel (.xlsx)",
                data=buffer_excel.getvalue(),
                file_name=f"budget_{annee_sel}_{mois_sel[:2]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with exp_col2:
            pdf_data = generate_pdf(df_m, f"{mois_sel} {annee_sel}", tot_entrees, tot_sorties, report_n_1, solde_mois, solde_final)
            st.download_button(
                label="📄 Télécharger le rapport PDF (.pdf)",
                data=pdf_data,
                file_name=f"budget_{annee_sel}_{mois_sel[:2]}.pdf",
                mime="application/pdf"
            )

        st.divider()

        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Ventilation des dépenses")
            df_dep = df_m[df_m["sorties"] > 0]
            if not df_dep.empty:
                fig_pie = px.pie(df_dep, values="sorties", names="categorie", hole=0.35, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with g2:
            st.subheader("Détail des Frais Fixes")
            if not df_ff.empty:
                fig_ff = px.bar(df_ff, x="sorties", y="categorie", orientation='h', color="categorie")
                fig_ff.update_layout(showlegend=False)
                st.plotly_chart(fig_ff, use_container_width=True)

with tab2:
    if not df.empty:
        annee_a = st.selectbox("Année d'analyse", sorted(df['Annee'].unique(), reverse=True), key="a_key")
        df_an = df[df['Annee'] == annee_a].copy()
        df_an['Mois_Num'] = df_an['date'].dt.month
        df_an['Mois_Nom'] = df_an['date'].dt.strftime('%b')
        
        df_bar = df_an.groupby(['Mois_Num', 'Mois_Nom'])[['entrees', 'sorties']].sum().reset_index()
        
        st.subheader("Entrées vs Dépenses par mois")
        fig_bar = px.bar(df_bar, x='Mois_Nom', y=['entrees', 'sorties'], barmode='group', color_discrete_map={'entrees': '#2ecc71', 'sorties': '#e74c3c'})
        st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader("⚙️ Gestion des Reports de Mois Précédent (N-1)")
    with st.form("form_report"):
        rep_period = st.text_input("Période Mois Précédent (Format YYYY-MM, ex: 2026-07)", value=f"{prev_annee_mois}")
        rep_valeur = st.number_input("Montant du Report (€)", value=float(report_n_1), step=50.0, format="%.2f")
        if st.form_submit_button("💾 Enregistrer le Report"):
            set_report(rep_period, rep_valeur)
            st.success(f"Report pour {rep_period} mis à jour à {rep_valeur:.2f} €")
            st.rerun()

    st.divider()
    if not df.empty:
        st.subheader("Historique des écritures")
        st.dataframe(df.sort_values("date", ascending=False)[['id', 'date', 'categorie', 'type', 'libelle', 'sorties', 'entrees']], use_container_width=True)
        
        st.divider()
        st.subheader("Supprimer une ligne")
        del_id = st.number_input("Entrez l'ID de la ligne", min_value=1, step=1)
        if st.button("Supprimer"):
            delete_operation(del_id)
            st.success(f"Ligne {del_id} supprimée.")
            st.rerun()