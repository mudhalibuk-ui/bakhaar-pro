import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime
import plotly.express as px

# --- 1. PAGE CONFIG & ADVANCED CSS (Image-like Design) ---
st.set_page_config(page_title="Bakhaar Pro Dashboard", layout="wide")

st.markdown("""
    <style>
    /* Background-ka Guud */
    .main { background-color: #f0f2f6; }
    
    /* Sidebar-ka Madow ee sawirkaaga cml */
    [data-testid="stSidebar"] {
        background-color: #1a2a44 !important;
        color: white;
    }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Kaararka Cad-cad (White Cards with Shadow) */
    .metric-card {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: left;
        border-bottom: 4px solid #2563eb;
    }
    
    .metric-title { color: #64748b; font-size: 14px; font-weight: 600; }
    .metric-value { color: #1e293b; font-size: 28px; font-weight: 800; }
    
    /* Badhamada (Orange/Blue Buttons) */
    .stButton>button {
        background-color: #ff9800; /* Orange midabka sawirka ku jira */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & AUTH ---
DB_URL = st.secrets["db_url"]
def get_connection(): return psycopg2.connect(DB_URL)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Shaashadda Login-ka oo la qurxiyey
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🚀 Bakhaar Master")
        u = st.text_input("Username")
        p = st.text_input("Password", type='password')
        if st.button("Gasho"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=%s AND password=%s", (u, p))
            res = c.fetchone()
            if res:
                st.session_state.logged_in = True
                st.session_state.user_role, st.session_state.username = res[0], u
                st.rerun()
            else: st.error("Khaldan!")
else:
    # --- SIDEBAR (Sawirkaaga cml) ---
    st.sidebar.markdown(f"### 👤 {st.session_state.username}")
    menu = ["🏠 Home", "📦 Inventory", "🛒 Sales", "👥 Employees", "⚙️ Settings"]
    choice = st.sidebar.radio("Navigation", menu)

    conn = get_connection()

    # --- 📊 DASHBOARD (Home) ---
    if "Home" in choice:
        st.title("Dashboard User")
        
        # Kaararka Sare (Sida sawirkaaga: Earning, Share, etc.)
        df_stock = pd.read_sql("SELECT * FROM stock", conn)
        df_sales = pd.read_sql("SELECT * FROM sales", conn)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Earnings</p><p class='metric-value'>${df_sales['wadarta'].sum():,.0f}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Stock items</p><p class='metric-value'>{len(df_stock)}</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Total Sales</p><p class='metric-value'>{len(df_sales)}</p></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Rating</p><p class='metric-value'>8,5 ⭐</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Garaafyada (Bar Chart iyo Area Chart sida sawirka)
        col_left, col_right = st.columns([2,1])
        
        with col_left:
            st.markdown("### Result (Sales Performance)")
            if not df_sales.empty:
                df_sales['taariikh'] = pd.to_datetime(df_sales['taariikh'])
                fig = px.bar(df_sales, x=df_sales['taariikh'].dt.strftime('%b'), y='wadarta', 
                             color_discrete_sequence=['#1a2a44'], barmode='group')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Trend Analysis")
            if not df_sales.empty:
                fig2 = px.area(df_sales, x='taariikh', y='wadarta', color_discrete_sequence=['#ff9800'])
                st.plotly_chart(fig2, use_container_width=True)

        with col_right:
            st.markdown("### Goal Completion")
            # Doughnut chart sida sawirka 45%
            fig3 = px.pie(values=[45, 55], names=['Done', 'Left'], hole=0.7, 
                          color_discrete_sequence=['#1a2a44', '#f0f2f6'])
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("<div style='text-align:center;'><b>45% of Monthly Target</b></div>", unsafe_allow_html=True)

    # --- Qaybihii kale (Inventory, POS, HRM) ku dar halkan sidii code-kii hore ---
    elif "Inventory" in choice:
        st.title("📦 Inventory Management")
        st.dataframe(pd.read_sql("SELECT * FROM stock", conn), use_container_width=True)
        
    elif "Sales" in choice:
        st.title("🛒 POS System")
        st.write("Halkan ka sameey iib cusub...")

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()