import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Bakhaar Pro ERP", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #1a2a44 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-bottom: 5px solid #ff9800;
    }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & EMAIL FUNCTIONS ---
DB_URL = st.secrets["db_url"]

def send_email_report(receiver_email, subject, body):
    try:
        sender_email = st.secrets["email_user"]
        password = st.secrets["email_pass"]
        
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

def init_db():
    conn = psycopg2.connect(DB_URL)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stock (id SERIAL PRIMARY KEY, alaab TEXT, tirada INTEGER, qiimaha REAL, row_loc TEXT, dept_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, alaab TEXT, tirada INTEGER, wadarta REAL, taariikh TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sold_by TEXT, store_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, magaca TEXT, booska TEXT, mushaarka REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS departments (id SERIAL PRIMARY KEY, store_name TEXT, location TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin') ON CONFLICT DO NOTHING")
    conn.commit()
    c.close()
    conn.close()

init_db()
def get_connection(): return psycopg2.connect(DB_URL)

# --- 3. AUTHENTICATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

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
                st.session_state.logged_in, st.session_state.user_role, st.session_state.username = True, res[0], u
                st.rerun()
            else: st.error("Macluumaad khaldan!")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- NAVIGATION ---
    st.sidebar.markdown(f"## 👤 {st.session_state.username}")
    menu = ["🏠 Home", "🏢 Departments", "📦 Inventory", "🛒 POS (Iibka)", "👥 HRM", "📊 Reports", "⚙️ Settings"]
    choice = st.sidebar.radio("Main Menu", menu)
    conn = get_connection()

    # --- 🏢 DEPARTMENTS ---
    if choice == "🏢 Departments":
        st.title("Store Locations")
        with st.form("dept_f"):
            s_name = st.text_input("Store Name")
            s_loc = st.text_input("Location")
            if st.form_submit_button("Save"):
                c = conn.cursor()
                c.execute("INSERT INTO departments (store_name, location) VALUES (%s, %s)", (s_name, s_loc))
                conn.commit()
                st.success("Waa la keydiyey!")
        st.dataframe(pd.read_sql("SELECT * FROM departments", conn), use_container_width=True)

    # --- 📊 REPORTS & EMAIL ---
    elif choice == "📊 Reports":
        st.title("Reports & Email Alerts")
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        
        if not df_sales.empty:
            st.subheader("Send Daily Report to Manager")
            target_email = st.text_input("Geli Email-ka Maareeyaha")
            if st.button("Send Report Now"):
                total_rev = df_sales['wadarta'].sum()
                report_body = f"Warbixinta Maanta:\n\nWadarta Iibka: ${total_rev:,.2f}\nTransactions: {len(df_sales)}\n\nNabad gelyo!"
                if send_email_report(target_email, "Daily Sales Report", report_body):
                    st.success("Email-ka waa la diray!")
            
            st.plotly_chart(px.bar(df_sales, x='store_name', y='wadarta', title="Dakhliga Dukaamada"))
        else:
            st.info("Wali wax iib ah ma dhicin.")

    # --- QAYBAHA KALE SIDII HORE ---
    elif choice == "🏠 Home":
        st.title("Dashboard Overview")
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        st.markdown(f"<div class='metric-card'><h3>Total Revenue: ${df_sales['wadarta'].sum():,.2f}</h3></div>", unsafe_allow_html=True)

    elif choice == "🛒 POS (Iibka)":
        st.title("Point of Sale")
        depts = pd.read_sql("SELECT store_name FROM departments", conn)
        df_stock = pd.read_sql("SELECT * FROM stock WHERE tirada > 0", conn)
        if not depts.empty and not df_stock.empty:
            with st.form("p_f"):
                st_sel = st.selectbox("Store", depts['store_name'])
                it_sel = st.selectbox("Item", df_stock['alaab'])
                q_sel = st.number_input("Qty", min_value=1)
                if st.form_submit_button("Submit"):
                    row = df_stock[df_stock['alaab'] == it_sel].iloc[0]
                    total = q_sel * row['qiimaha']
                    c = conn.cursor()
                    c.execute("UPDATE stock SET tirada = tirada - %s WHERE id = %s", (q_sel, int(row['id'])))
                    c.execute("INSERT INTO sales (alaab, tirada, wadarta, sold_by, store_name) VALUES (%s,%s,%s,%s,%s)", 
                              (it_sel, q_sel, total, st.session_state.username, st_sel))
                    conn.commit()
                    st.success("Iibka waa la xareeyay!")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()