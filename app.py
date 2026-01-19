import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Bakhaar Pro ERP", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #1a2a44 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .metric-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-bottom: 5px solid #ff9800;
    }
    .card { background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE INITIALIZATION ---
DB_URL = st.secrets["db_url"]

def get_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Abuuritaanka dhamaan Tables-ka loo baahan yahay
    c.execute("CREATE TABLE IF NOT EXISTS departments (id SERIAL PRIMARY KEY, store_name TEXT, location TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS stock (id SERIAL PRIMARY KEY, alaab TEXT, tirada INTEGER, qiimaha REAL, row_loc TEXT, store_name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, alaab TEXT, tirada INTEGER, wadarta REAL, taariikh TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sold_by TEXT, store_name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, magaca TEXT, booska TEXT, mushaarka REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)")
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin') ON CONFLICT DO NOTHING")
    conn.commit()
    c.close()
    conn.close()

# Isku day in la kiciyo Database-ka
try:
    init_db()
except Exception as e:
    st.error(f"Database Initialization Error: {e}")

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
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("Username ama Password waa khaldan!")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- NAVIGATION ---
    st.sidebar.title("📦 Bakhaar Pro")
    menu = ["🏠 Home", "🏢 Departments", "📦 Inventory", "🛒 POS (Iibka)", "👥 HRM", "📊 Reports", "⚙️ Settings"]
    choice = st.sidebar.radio("Main Menu", menu)
    
    conn = get_connection()

    # --- 🏠 HOME ---
    if choice == "🏠 Home":
        st.title("Dashboard Overview")
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><small>Total Revenue</small><h3>${df_sales['wadarta'].sum() if not df_sales.empty else 0:,.2f}</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>Transactions</small><h3>{len(df_sales)}</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><small>Status</small><h3>Active</h3></div>", unsafe_allow_html=True)

    # --- 🏢 DEPARTMENTS ---
    elif choice == "🏢 Departments":
        st.title("Manage Stores")
        with st.form("dept_form"):
            s_name = st.text_input("Store Name")
            s_loc = st.text_input("Location")
            if st.form_submit_button("Save Store"):
                c = conn.cursor()
                c.execute("INSERT INTO departments (store_name, location) VALUES (%s, %s)", (s_name, s_loc))
                conn.commit()
                st.success("Store added!")
        st.dataframe(pd.read_sql("SELECT * FROM departments", conn), use_container_width=True)

    # --- 📦 INVENTORY ---
    elif choice == "📦 Inventory":
        st.title("Inventory Management")
        depts = pd.read_sql("SELECT store_name FROM departments", conn)
        with st.form("inv_form"):
            name = st.text_input("Item Name")
            qty = st.number_input("Quantity", min_value=1)
            prc = st.number_input("Price", min_value=0.0)
            st_name = st.selectbox("Store", depts['store_name']) if not depts.empty else st.text_input("Store Name")
            if st.form_submit_button("Add Item"):
                c = conn.cursor()
                c.execute("INSERT INTO stock (alaab, tirada, qiimaha, store_name) VALUES (%s,%s,%s,%s)", (name, qty, prc, st_name))
                conn.commit()
                st.success("Item added to stock!")
        st.dataframe(pd.read_sql("SELECT * FROM stock", conn), use_container_width=True)

    # --- 🛒 POS ---
    elif choice == "🛒 POS (Iibka)":
        st.title("Point of Sale")
        df_stock = pd.read_sql("SELECT * FROM stock WHERE tirada > 0", conn)
        if not df_stock.empty:
            with st.form("sale_form"):
                item = st.selectbox("Select Item", df_stock['alaab'])
                sqty = st.number_input("Quantity", min_value=1)
                if st.form_submit_button("Sell"):
                    row = df_stock[df_stock['alaab'] == item].iloc[0]
                    total = sqty * row['qiimaha']
                    c = conn.cursor()
                    c.execute("UPDATE stock SET tirada = tirada - %s WHERE id = %s", (sqty, int(row['id'])))
                    c.execute("INSERT INTO sales (alaab, tirada, wadarta, sold_by, store_name) VALUES (%s,%s,%s,%s,%s)", 
                              (item, sqty, total, st.session_state.username, row['store_name']))
                    conn.commit()
                    st.success(f"Sold! Total: ${total}")
        else: st.warning("Stock is empty!")

    # --- 👥 HRM ---
    elif choice == "👥 HRM":
        st.title("Employee Management")
        with st.form("hrm_form"):
            en = st.text_input("Employee Name")
            eb = st.text_input("Role")
            if st.form_submit_button("Register"):
                c = conn.cursor()
                c.execute("INSERT INTO employees (magaca, booska) VALUES (%s,%s)", (en, eb))
                conn.commit()
                st.success("Registered!")
        st.dataframe(pd.read_sql("SELECT * FROM employees", conn), use_container_width=True)

    # --- 📊 REPORTS ---
    elif choice == "📊 Reports":
        st.title("Sales Reports")
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        if not df_sales.empty:
            st.plotly_chart(px.bar(df_sales, x='alaab', y='wadarta', title="Sales per Item"))
            st.dataframe(df_sales)
        else: st.info("No sales data.")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()