import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Bakhaar & HRM Master", layout="wide")

# Ka soo qaado URL-ka Database-ka Secrets-ka Streamlit
try:
    DB_URL = st.secrets["db_url"]
except:
    st.error("Fadlan ku dar 'db_url' qaybta Secrets ee Streamlit Settings!")
    st.stop()

def get_connection():
    return psycopg2.connect(DB_URL)

# Abuurista Tables-ka haddii aysan jirin
def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Inventory Table
    c.execute('''CREATE TABLE IF NOT EXISTS stock 
                 (id SERIAL PRIMARY KEY, bakhaar TEXT, alaab TEXT, tirada INTEGER, 
                  qiimaha REAL, row_loc TEXT, shelf_loc TEXT, barcode TEXT)''')
    # Sales Table
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id SERIAL PRIMARY KEY, alaab TEXT, tirada INTEGER, wadarta REAL, 
                  taariikh TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sold_by TEXT)''')
    # HRM Table (Employees)
    c.execute('''CREATE TABLE IF NOT EXISTS employees 
                 (id SERIAL PRIMARY KEY, magaca TEXT, booska TEXT, mushaarka REAL, phone TEXT)''')
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # User-ka hore (Default Admin)
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin') ON CONFLICT DO NOTHING")
    conn.commit()
    c.close()
    conn.close()

init_db()

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Bakhaar & HRM Master AI")
    col_l, col_r = st.columns(2)
    with col_l:
        u = st.text_input("Username")
        p = st.text_input("Password", type='password')
        if st.button("Gasho"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=%s AND password=%s", (u, p))
            res = c.fetchone()
            if res:
                st.session_state.logged_in = True
                st.session_state.user_role = res[0]
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Username ama Password waa khaldan!")
else:
    # --- 3. SIDEBAR NAVIGATION ---
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"Darajada: {st.session_state.user_role}")
    
    if st.session_state.user_role == "Admin":
        menu = ["Dashboard & Map", "Inventory (Stock)", "POS (Iibka)", "HRM (Shaqaalaha)", "Settings"]
    else:
        menu = ["Dashboard & Map", "POS (Iibka)"]
        
    choice = st.sidebar.radio("Xulo Qaybta", menu)