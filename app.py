import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; border: none; padding: 0.6rem 2.5rem; font-weight: 500;
    }
    div.stButton > button:disabled {
        background: #333537 !important; color: #757575 !important; cursor: not-allowed;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize State ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Status": "Waiting", "Draft": ""}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. API Connector (Standard Path) ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ส่งข้อมูลให้ตรงกับ Node Start ในภาพ image_18f01b.png
    payload = {
        "inputs": {
            "Topic": str(topic),
            "Guide": str(guide),
            "Persona": "กะเทย เล่น rov มานาน"
        },
        "response_mode": "blocking",
        "user": "gemini_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        if 'error' in res_data:
            st.error(f"❌ API Error: {res_data['error'].get('message')}")
            return []

        # ดึง Output จาก Node End
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output:
            st.warning("⚠️ AI ไม่ตอบกลับ (อย่าลืมกด Publish ใน Insea และเติมช่อง User Message นะครับ)")
            return []

        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except Exception as e:
        st.error(f"📡 Connection Error: {str(e)}")
        return []

# --- 4. Login Section (Fix Unlock Button) ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    u = st.text_input("Garena Email", placeholder="Email")
    p = st.text_input("Password", type="password")
    
    # REQUIRE: ต้องกรอกครบ ปุ่ม Sign In ถึงจะหายล็อค
    login_ready = u.strip() != "" and p.strip() != ""
    
    if st.button("Sign In", disabled=not login_ready):
        if u == "kittikoon.k@garena.com" and p == "garena123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("ข้อมูล Login ไม่ถูกต้อง")
    
    if not login_ready:
        st.caption("🔒 โปรดกรอกข้อมูลให้ครบเพื่อปลดล็อคปุ่ม")

else:
    # --- 5. Workspace ---
    st.sidebar.title(f"💎 คุณกิตติคุณ")
    page = st.sidebar.radio("Navigate:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    if page == "PIC Workspace":
        st.title("📱 PIC Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('กำลังรอ AI...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res: st.session_state[f"res_{t['id']}"] = res

                if f"res_{t['id']}" in st.session_state:
                    for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                t['Draft'] = st.text_area("Final Draft (Require)", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                
                if st.button("Submit (ส่งงาน)", key=f"sub_{t['id']}", disabled=not t['Draft'].strip()):
                    t['Status'] = "Done"
                    st.success("ส่งงานสำเร็จ!")
