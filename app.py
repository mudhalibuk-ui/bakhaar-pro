import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px

# --- 1. CONFIG & STYLING (Sawirkaaga cml) ---
st.set_page_config(page_title="Bakhaar Pro ERP", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #1a2a44 !important; }
    [data-testid="stSidebar"] * { color: white !important; font-size: 16px; }
    
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-bottom: 5px solid #2563eb;
    }
    .stButton>button {
        background-color: #ff9800;
        color: white;
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
    }
    .card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
DB_URL = st.secrets["db_url"]
def get_connection(): return psycopg2.connect(DB_URL)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. AUTHENTICATION ---
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
    # --- NAVIGATION (Icons added) ---
    st.sidebar.markdown(f"## 👤 {st.session_state.username}")
    menu = {
        "🏠 Home": "Home",
        "📦 Inventory": "Inventory",
        "🛒 POS (Iibka)": "POS",
        "👥 HRM (Shaqaalaha)": "HRM",
        "⚙️ Settings": "Settings"
    }
    choice = st.sidebar.radio("Menu-ga", list(menu.keys()))

    conn = get_connection()

    # --- 📊 1. HOME (DASHBOARD) ---
    if "Home" in choice:
        st.title("Dashboard Overview")
        df_stock = pd.read_sql("SELECT * FROM stock", conn)
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='metric-card'><small>Earnings</small><h3>${df_sales['wadarta'].sum():,.0f}</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>Items in Stock</small><h3>{df_stock['tirada'].sum() if not df_stock.empty else 0}</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><small>Sales Count</small><h3>{len(df_sales)}</h3></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='metric-card'><small>Rating</small><h3>8.5 ⭐</h3></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns([2,1])
        with col_l:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            if not df_sales.empty:
                df_sales['taariikh'] = pd.to_datetime(df_sales['taariikh'])
                fig = px.area(df_sales, x='taariikh', y='wadarta', title="Sales Performance Trend", color_discrete_sequence=['#2563eb'])
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col_r:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            fig_pie = px.pie(values=[45, 55], names=['Goal', 'Remaining'], hole=0.7, color_discrete_sequence=['#ff9800', '#f1f5f9'])
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("<p style='text-align:center'>45% of Monthly Goal</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 📦 2. INVENTORY ---
    elif "Inventory" in choice:
        st.title("📦 Maamulka Stock-ka")
        t1, t2 = st.tabs(["📋 Liiska Alaabta", "➕ Ku dar Alaab"])
        with t2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            with st.form("inv_form"):
                name = st.text_input("Magaca Alaabta")
                qty = st.number_input("Tirada", min_value=1)
                price = st.number_input("Qiimaha", min_value=0.0)
                loc = st.text_input("Shelf Location (tusaale: A1)")
                if st.form_submit_button("Keydi"):
                    c = conn.cursor()
                    c.execute("INSERT INTO stock (alaab, tirada, qiimaha, row_loc) VALUES (%s,%s,%s,%s)", (name, qty, price, loc))
                    conn.commit()
                    st.success("Waa la keydiyey!")
            st.markdown("</div>", unsafe_allow_html=True)
        with t1:
            df_stock = pd.read_sql("SELECT * FROM stock", conn)
            st.dataframe(df_stock, use_container_width=True)

    # --- 🛒 3. POS ---
    elif "POS" in choice:
        st.title("🛒 Point of Sale")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        df_stock = pd.read_sql("SELECT * FROM stock WHERE tirada > 0", conn)
        if not df_stock.empty:
            item = st.selectbox("Xulo Alaabta", df_stock['alaab'])
            sqty = st.number_input("Tirada Iibka", min_value=1)
            if st.button("Dhameystir Iibka"):
                row = df_stock[df_stock['alaab'] == item].iloc[0]
                total = sqty * row['qiimaha']
                c = conn.cursor()
                c.execute("UPDATE stock SET tirada = tirada - %s WHERE id = %s", (sqty, int(row['id'])))
                c.execute("INSERT INTO sales (alaab, tirada, wadarta, sold_by) VALUES (%s,%s,%s,%s)", (item, sqty, total, st.session_state.username))
                conn.commit()
                st.balloons()
                st.success(f"Iibku wuu dhacay! Wadarta: ${total}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 👥 4. HRM ---
    elif "HRM" in choice:
        st.title("👥 Maamulka Shaqaalaha")
        t1, t2 = st.tabs(["📋 Liiska Shaqaalaha", "➕ Diiwaangeli"])
        with t2:
            with st.form("hrm_f"):
                n = st.text_input("Magaca")
                b = st.text_input("Booska")
                s = st.number_input("Mushaarka", min_value=0)
                if st.form_submit_button("Diiwaangeli"):
                    c = conn.cursor()
                    c.execute("INSERT INTO employees (magaca, booska, mushaarka) VALUES (%s,%s,%s)", (n, b, s))
                    conn.commit()
                    st.success("Shaqaale cusub waa la daray!")
        with t1:
            df_emp = pd.read_sql("SELECT * FROM employees", conn)
            st.table(df_emp)

    # --- ⚙️ 5. SETTINGS ---
    elif "Settings" in choice:
        st.title("⚙️ Settings")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        new_pass = st.text_input("Beddel Password-ka", type="password")
        if st.button("Cusboonaysii"):
            c = conn.cursor()
            c.execute("UPDATE users SET password=%s WHERE username=%s", (new_pass, st.session_state.username))
            conn.commit()
            st.success("Password-kii waa la beddelay!")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()