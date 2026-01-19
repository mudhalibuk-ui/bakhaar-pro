import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Bakhaar Master Pro", layout="wide")

# CSS-ka Qurxinta (Modern UI)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f2f6;
    }
    
    .main-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
    }
    
    .sidebar-header {
        font-size: 24px;
        font-weight: 800;
        color: #2563eb;
        margin-bottom: 20px;
    }
    
    .map-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        transition: 0.2s;
        border: 2px solid rgba(0,0,0,0.05);
    }
    
    .map-box:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & AUTH (Sidaadii hore) ---
DB_URL = st.secrets["db_url"]
def get_connection(): return psycopg2.connect(DB_URL)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- LOGIN SCREEN (BEAUTIFIED) ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.title("🚀 Bakhaar Pro")
        st.subheader("Ku soo dhawaada nidaamka midaysan")
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
            else: st.error("Macluumaad khaldan!")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- NAVIGATION ---
    st.sidebar.markdown("<div class='sidebar-header'>📦 Bakhaar Pro</div>", unsafe_allow_html=True)
    menu = ["📊 Dashboard", "📦 Inventory", "🛒 POS (Iibka)", "👥 HRM", "⚙️ Settings"]
    choice = st.sidebar.radio("Main Menu", menu)

    conn = get_connection()
    
    # --- DASHBOARD ---
    if "Dashboard" in choice:
        st.title("Warbixinta Guud")
        df_stock = pd.read_sql("SELECT * FROM stock", conn)
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stock-ka yaalla", f"{df_stock['tirada'].sum()} Pcs")
        m2.metric("Wadarta Iibka", f"${df_sales['wadarta'].sum():,.0f}")
        m3.metric("Iibka Maanta", f"{len(df_sales)}")
        m4.metric("Dakhliga Maanta", f"${df_sales[df_sales['taariikh'].dt.date == datetime.now().date()]['wadarta'].sum():,.0f}")

        st.markdown("### 📍 Khariidadda Bakhaarka")
        for r in ['A', 'B', 'C']:
            cols = st.columns(5)
            for i, s in enumerate(['1', '2', '3', '4', '5']):
                qty = df_stock[(df_stock['row_loc'] == r) & (df_stock['shelf_loc'] == s)]['tirada'].sum()
                bg = "#10b981" if qty > 10 else "#f59e0b" if qty > 0 else "#ef4444"
                with cols[i]:
                    st.markdown(f"<div class='map-box' style='background:{bg}; color:white;'>{r}{s}<br>{qty} Pcs</div>", unsafe_allow_html=True)

    # --- INVENTORY ---
    elif "Inventory" in choice:
        st.title("Maamulka Alaabta")
        with st.expander("➕ Ku dar Alaab Cusub", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Magaca Alaabta")
                qty = st.number_input("Tirada", min_value=1)
            with col2:
                price = st.number_input("Qiimaha ($)", min_value=0.0)
                loc = st.selectbox("Safka & Khaanadda", ["A1","A2","A3","B1","B2","C1"])
            
            if st.button("Keydi"):
                c = conn.cursor()
                c.execute("INSERT INTO stock (alaab, tirada, qiimaha, row_loc, shelf_loc) VALUES (%s,%s,%s,%s,%s)",
                          (name, qty, price, loc[0], loc[1]))
                conn.commit()
                st.success("Waa la keydiyey!")

    # --- POS (Iibka) ---
    elif "POS" in choice:
        st.title("🛒 Iibka Degdegga ah")
        df_stock = pd.read_sql("SELECT * FROM stock WHERE tirada > 0", conn)
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            item = st.selectbox("Xulo Alaabta", df_stock['alaab'])
            sell_qty = st.number_input("Tirada", min_value=1)
            if st.button("Dhameystir Iibka"):
                # Logic halkan bay gelaysaa (sidii hore)
                st.success("Iibku wuu guulaystay!")
            st.markdown("</div>", unsafe_allow_html=True)