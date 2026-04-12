import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from main import run_agent
from database import save_preferences, init_db, get_preferences

# 1. Initialize Database
init_db()

# 2. Page Configuration
st.set_page_config(page_title="AI Travel Pro", layout="wide", page_icon="✈️")

# 3. Premium CSS (Light, Airy, and Professional)
st.markdown("""
    <style>
    /* تغيير خلفية التطبيق لتدرج لوني خفيف جداً يريح العين */
    .stApp {
        background: linear-gradient(135deg, #f0f6ff 0%, #ffffff 100%);
    }
    
    /* تنظيف الـ Sidebar */
    [data-testid="stSidebarNav"] {
        padding-top: 0rem;
    }
    [data-testid="stSidebar"] {
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }

    /* تصميم زر البحث (Explore) ليكون متدرج و 3D */
    .stButton>button {
        background: linear-gradient(90deg, #0ea5e9, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.4) !important;
        transition: all 0.3s ease !important;
        margin-top: 28px;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(14, 165, 233, 0.6) !important;
    }

    /* تنسيق مربع نتائج الـ Agent ليكون زي الـ Paper */
    div[data-testid="stAlert"] {
        background-color: white !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
        color: #1e293b !important;
    }
    
    /* تنسيق مربعات الإدخال */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. Sidebar - Personal Settings
with st.sidebar:
    st.title("⚙️ Personal Settings")
    
    current_prefs = get_preferences("user_1")
    default_airline = current_prefs[1] if current_prefs else "Any"
    default_budget = float(current_prefs[3]) if current_prefs else 2000.0

    airline_pref = st.selectbox("Preferred Airline", ["Any", "Emirates", "Qatar Airways", "EgyptAir", "Saudia"], 
                                index=["Any", "Emirates", "Qatar Airways", "EgyptAir", "Saudia"].index(default_airline))
    
    budget_pref = st.number_input("Budget Limit (AED)", value=default_budget)

    if st.button("Save Settings"):
        save_preferences("user_1", airline_pref, "Window", budget_pref)
        st.success("Saved Successfully! ✅")
    
    st.divider()
    st.caption("AI Travel Agent V2.0")

# 5. Top Search Interface
st.write("### 🌍 Discover Your Next Flight")
with st.container():
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1: origin = st.text_input("From", placeholder="DXB")
    with c2: dest = st.text_input("To", placeholder="CAI")
    with c3: dep_date = st.date_input("Departure Date", value=date(2026, 4, 27))
    with c4: 
        search_btn = st.button("Explore 🚀", use_container_width=True)

direct = st.checkbox("Direct flights only")

st.divider()

# 6. Search Results (Clean, Full Width)
if search_btn:
    if not origin or not dest:
        st.warning("Please enter both origin and destination cities.")
    else:
        user_input = f"Search for a flight from {origin} to {dest} on {dep_date}."
        stop_pref = 0 if direct else None
        context = f"\n[Context: Budget {budget_pref} AED, Stops Pref: {stop_pref}, Airline Pref: {airline_pref}]"
        
        with st.status("🤖 Agent is analyzing..."):
            response = run_agent(user_input + context)
            
        st.write("#### 📋 Search & Analysis Results:")
        st.info(response)
else:
    st.write("Start searching to display results here...")