import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px

# --- 1. PAGE CONFIG & MODERN CSS ---
st.set_page_config(page_title="Bakhaar Pro ERP", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; border-top: 5px solid #2563eb; }
    .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
DB_URL = st.secrets["db_url"]
def get_connection():
    return psycopg2.connect(DB_URL)

# --- 3. AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.title("🔐 Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type='password')
        if st.button("Gasho System-ka"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=%s AND password=%s", (u, p))
            res = c.fetchone()
            if res:
                st.session_state.logged_in = True
                st.session_state.user_role, st.session_state.username = res[0], u
                st.rerun()
            else: st.error("Username ama Password waa khaldan!")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("📦 Bakhaar Pro")
    st.sidebar.markdown(f"**User:** {st.session_state.username}")
    menu = ["📊 Dashboard", "📦 Inventory", "🛒 POS (Iibka)", "👥 HRM (Shaqaalaha)", "⚙️ Settings"]
    choice = st.sidebar.radio("Main Menu", menu)

    conn = get_connection()

    # --- DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("Halkan ka eeg xaaladda ganacsiga")
        df_stock = pd.read_sql("SELECT * FROM stock", conn)
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        
        if not df_sales.empty:
            df_sales['taariikh'] = pd.to_datetime(df_sales['taariikh'])
            maanta = datetime.now().date()
            d_maanta = df_sales[df_sales['taariikh'].dt.date == maanta]['wadarta'].sum()
        else: d_maanta = 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Stock-ka", f"{df_stock['tirada'].sum() if not df_stock.empty else 0} Pcs")
        c2.metric("Wadarta Iibka", f"${df_sales['wadarta'].sum() if not df_sales.empty else 0:,.0f}")
        c3.metric("Iibka Maanta", f"${d_maanta:,.0f}")

        # Visual Analytics
        if not df_sales.empty:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            fig = px.line(df_sales, x='taariikh', y='wadarta', title="Kobaca Iibka (Sales Trend)")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- HRM (SHAQAALAHA) ---
    elif choice == "👥 HRM (Shaqaalaha)":
        st.title("Maamulka Shaqaalaha")
        t1, t2 = st.tabs(["📋 Diiwaanka Shaqaalaha", "➕ Ku dar Shaqaale"])
        
        with t2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            with st.form("new_emp"):
                name = st.text_input("Magaca")
                pos = st.text_input("Booska (Role)")
                sal = st.number_input("Mushaarka ($)", min_value=0)
                if st.form_submit_button("Diiwaangeli"):
                    c = conn.cursor()
                    c.execute("INSERT INTO employees (magaca, booska, mushaarka) VALUES (%s,%s,%s)", (name, pos, sal))
                    conn.commit()
                    st.success("Shaqaale cusub waa la daray!")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with t1:
            df_emp = pd.read_sql("SELECT * FROM employees", conn)
            st.table(df_emp)

    # --- SETTINGS ---
    elif choice == "⚙️ Settings":
        st.title("Habaynta Nidaamka")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔑 Beddel Password-ka")
        new_p = st.text_input("Password Cusub", type="password")
        if st.button("Cusboonaysii"):
            c = conn.cursor()
            c.execute("UPDATE users SET password=%s WHERE username=%s", (new_p, st.session_state.username))
            conn.commit()
            st.success("Password-ka waa la beddelay!")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()