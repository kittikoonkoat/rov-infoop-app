import streamlit as st
import pandas as pd
import requests
import json
import re

# --- 1. UI Styling: Ultra Luxury Dark ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; border-right: 1px solid #333537; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important; color: #FFFFFF !important;
        border: 1px solid #444746 !important; border-radius: 12px !important;
    }
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; font-weight: 500; border: none; padding: 0.6rem 2.5rem;
    }
    .stInfo { background-color: #041E3C !important; color: #D3E3FD !important; border: 1px solid #0842A0 !important; border-radius: 14px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Database & Session ---
if 'db' not in st.session_state: st.session_state.db = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
users = {"kittikoon.k@garena.com": {"name": "คุณกิตติคุณ", "pass": "garena123"}}

# --- 3. The "Deep-Parsing" API Logic ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" #
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": "กะเทย เล่น rov มานาน"},
        "response_mode": "blocking",
        "user": "gemini_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # เจาะเข้าหา 'text' ตามรูป image_1aae73.png
        raw_text = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_text:
            return []

        # แก้ปัญหาเรื่อง \n ที่มาเป็นตัวอักษร ไม่ใช่บรรทัดใหม่
        clean_text = str(raw_text).replace('\\n', '\n')
        
        # แยกข้อความ (หาบรรทัดที่มีข้อความยาวๆ)
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        
        # ลบเลขข้อด้านหน้าออก (เช่น 1., 2.)
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except:
        return []

# --- 4. Main Flow ---
if not st.session_state.logged_in:
    st.title("✨ Sign in")
    with st.form("login"):
        u = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            if u in users and users[u]['pass'] == p:
                st.session_state.logged_in = True
                st.session_state.user_info = users[u]
                st.rerun()
else:
    user = st.session_state.user_info
    st.sidebar.write(f"💎 {user['name']}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📱 My Workspace")
    
    # ตัวอย่างงาน (ถ้ายังไม่มีใน DB)
    if not st.session_state.db:
        st.session_state.db.append({"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Draft": ""})

    for t in st.session_state.db:
        with st.expander(f"📌 {t['Topic']}", expanded=True):
            st.write(f"**แนวทาง:** {t['Guide']}")
            
            if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                with st.spinner('กำลังเจาะข้อมูล...'):
                    res = call_seeding_agent(t['Topic'], t['Guide'])
                    if res:
                        st.session_state[f"res_{t['id']}"] = res
                    else:
                        st.error("AI ยังไม่ส่งข้อมูล (ลองกด Publish ใน Insea อีกรอบครับ)")

            if f"res_{t['id']}" in st.session_state:
                for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                    st.info(msg)
                    if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
            
            t['Draft'] = st.text_area("Final Draft", value=t['Draft'], key=f"ed_{t['id']}")
            if st.button("ยืนยันส่งงาน", key=f"sub_{t['id']}"):
                st.success("ส่งงานสำเร็จ!")
