import streamlit as st
import pandas as pd
import requests

# --- 1. Gemini Luxury Dark UI Styling ---
st.set_page_config(page_title="RoV Seeding - Gemini Edition", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global Background (Gemini Dark) */
    .stApp {
        background-color: #131314;
        color: #E3E3E3;
    }
    
    html, body, [class*="css"] { 
        font-family: 'Inter', -apple-system, sans-serif; 
    }

    /* Sidebar - Deep Space */
    [data-testid="stSidebar"] {
        background-color: #1E1F20 !important;
        border-right: 1px solid #333537;
    }

    /* Luxury Input Fields & Text Areas */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important;
        color: #FFFFFF !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-size: 15px !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #8E918F !important;
        box-shadow: 0 0 0 1px #8E918F !important;
    }

    /* Gemini Gradient Buttons */
    div.stButton > button {
        border-radius: 24px;
        background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 2.5rem;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        box-shadow: 0 0 15px rgba(66, 133, 244, 0.4);
        transform: translateY(-1px);
    }

    /* Glassmorphism Expanders */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
        margin-bottom: 15px;
    }

    /* AI Output Styling (High Visibility) */
    .stInfo {
        background-color: #041E3C !important;
        color: #D3E3FD !important;
        border: 1px solid #0842A0 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }

    /* High Contrast Metrics */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; }
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Storage ---
if 'users' not in st.session_state:
    st.session_state.users = {
        "kittikoon.k@garena.com": {"name": "คุณกิตติคุณ", "role": "Admin", "pass": "garena123"},
        "rov.pichsinee@garena.com": {"name": "น้องปลาย", "role": "PIC", "pass": "rov01"},
        "rov.jirapat@garena.com": {"name": "น้องกร", "role": "PIC", "pass": "rov02"},
        "rov.chaiwat@garena.com": {"name": "น้องเต้ย", "role": "PIC", "pass": "rov03"},
        "rov.thanakrit@garena.com": {"name": "น้องไทม์", "role": "PIC", "pass": "rov04"}
    }
if 'db' not in st.session_state: st.session_state.db = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. API Connection (Optimized for 'text' output) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "gemini_lux_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        outputs = result.get('data', {}).get('outputs', {})
        # ดึงจาก key 'text' ตามรูป image_1b96d8.png
        raw_text = outputs.get('text') or next(iter(outputs.values()), "")
        
        if not raw_text: return []
        
        # แยกข้อความ 10 ข้อที่ AI ส่งมา
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except:
        return []

# --- 4. Login System ---
if not st.session_state.logged_in:
    st.markdown("<br><h1 style='text-align: center;'>✨ RoV Seeding Portal</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        with st.form("login"):
            u_email = st.text_input("Garena Email")
            u_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if u_email in st.session_state.users and st.session_state.users[u_email]["pass"] == u_pass:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[u_email]
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")
    st.stop
