import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling: Ultra Clean Gemini Dark ---
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
        color: white; border: none; padding: 0.6rem 2.5rem; font-weight: 500;
    }
    .stInfo { background-color: #041E3C !important; color: #D3E3FD !important; border: 1px solid #0842A0 !important; border-radius: 14px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize DB & State ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Status": "Waiting", "Draft": ""}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. API Connector (Fixed Parsing) ---
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
        
        # เจาะเข้าหา 'text'
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output: return []

        # แก้ปัญหา \n ใน JSON String
        clean_text = str(raw_output).replace('\\n', '\n')
        
        # แยกบรรทัดและล้างเลขลำดับ
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return []

# --- 4. Main Flow ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    with st.form("login"):
        u = st.text_input("Garena Email")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            if u == "kittikoon.k@garena.com" and p == "garena123":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
else:
    # Sidebar Navigation (Force Show All for Admin)
    st.sidebar.title("💎 Navigation")
    choice = st.sidebar.radio("Go to:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- Page 1: PIC Workspace ---
    if choice == "PIC Workspace":
        st.title("📱 PIC Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('กำลังดึงข้อมูลจาก Insea...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res:
                            st.session_state[f"res_{t['id']}"] = res
                        else:
                            st.warning("AI ไม่ตอบกลับ (ตรวจสอบการ Publish ใน Insea นะคร้าบ)")

                # FIXED: Syntax Error จากรูป 1b39b3
                res_key = f"res_{t['id']}"
                if res_key in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[res_key]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                            st.success(f"เลือกข้อความที่ {i+1} แล้ว")
                
                t['Draft'] = st.text_area("Final Draft", value=t['Draft'], key=f"ed_{t['id']}", height=100)
                if st.button("Submit (ยืนยันส่งงาน)", key=f"sub_{t['id']}"):
                    t['Status'] = "Completed"
                    st.success("ส่งงานสำเร็จ!")

    # --- Page 2: Admin Control ---
    elif choice == "Admin Control":
        st.title("👨‍💻 Admin Control")
        with st.form("new_task"):
            nt = st.text_input("หัวข้อ (Topic)")
            ng = st.text_area("แนวทาง (Guideline)")
            if st.form_submit_button("Assign"):
                st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "Status": "Waiting", "Draft": ""})
                st.success("เพิ่มงานใหม่แล้ว")

    # --- Page 3: Daily Report ---
    elif choice == "Daily Report":
        st.title("📊 Daily Summary")
        if st.session_state.db:
            st.table(pd.DataFrame(st.session_state.db))
