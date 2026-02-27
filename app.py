import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling: Ultra Luxury Gemini Dark ---
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

# --- 2. Initialize Data & Auth ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Status": "Waiting", "Draft": ""}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. API Connector (Fixed Parsing from image_1aae73) ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" # Key จากคุณกิตติคุณ
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": "กะเทย เล่น rov มานาน"},
        "response_mode": "blocking",
        "user": "gemini_final_fix"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # ดึงค่า text จากโครงสร้าง data -> outputs -> text
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output: return []

        # แก้ปัญหา \n ที่มาเป็นตัวอักษร
        clean_text = str(raw_output).replace('\\n', '\n')
        
        # แยกเป็นข้อๆ และล้างเลขข้อ 1., 2.
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except:
        return []

# --- 4. Navigation Flow ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    with st.form("login_form"):
        u = st.text_input("Garena Email")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            if u == "kittikoon.k@garena.com" and p == "garena123":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้องครับ")
else:
    # Sidebar: แก้ปัญหาเมนูหายโดยใช้ Radio Button แทน
    st.sidebar.title("💎 Menu Control")
    page = st.sidebar.radio("Navigate to:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- PIC Workspace ---
    if page == "PIC Workspace":
        st.title("📱 My Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('กำลังร่างข้อความ...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res:
                            st.session_state[f"res_{t['id']}"] = res
                        else:
                            st.warning("AI ไม่ตอบกลับ (เช็คปุ่ม Publish ใน Insea นะครับ)")

                # FIXED: Syntax Error จากรูป image_1b39b3
                res_key = f"res_{t['id']}"
                if res_key in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[res_key]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                t['Draft'] = st.text_area("Final Draft", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                if st.button("Submit (ส่งงาน)", key=f"sub_{t['id']}"):
                    t['Status'] = "Done"
                    st.success("ส่งงานเรียบร้อย!")

    # --- Admin Control ---
    elif page == "Admin Control":
        st.title("👨‍💻 Admin Panel")
        with st.form("new_task"):
            st.subheader("Assign New Task")
            nt = st.text_input("Topic")
            ng = st.text_area("Guideline")
            if st.form_submit_button("Deploy"):
                st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "Status": "Waiting", "Draft": ""})
                st.success("จ่ายงานสำเร็จ!")

    # --- Daily Report ---
    elif page == "Daily Report":
        st.title("📊 Summary Report")
        if st.session_state.db:
            st.table(pd.DataFrame(st.session_state.db))
