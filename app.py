import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; }
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; border: none; padding: 0.6rem 2.5rem;
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

# --- 3. API Connector (Fixed for VALIDATION_VIOLATION) ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # แก้ไข Payload: ส่งแบบชั้นเดียว (Flat JSON) ตามที่ API แจ้ง Error มา
    payload = {
        "Topic": str(topic),
        "Guide": str(guide),
        "Persona": "กะเทย เล่น rov มานาน",
        "response_mode": "blocking",
        "user": "gemini_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # จัดการกรณี API Error
        if 'error' in res_data:
            st.error(f"❌ API ปฏิเสธ: {res_data['error']['message']}")
            return []

        # ดึงข้อความ (Data Path อาจต่างกันในแต่ละ Workflow)
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        if not raw_output:
            # ลองหาในชั้นนอกสุดเผื่อ API ส่งกลับมาแบบ Flat
            raw_output = res_data.get('text', "")

        if not raw_output:
            st.warning("⚠️ AI ตอบกลับมาเป็นค่าว่าง")
            return []

        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except Exception as e:
        st.error(f"📡 Error: {str(e)}")
        return []

# --- 4. Login Logic (Fixed Unlock) ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    u = st.text_input("Garena Email", placeholder="kittikoon.k@garena.com")
    p = st.text_input("Password", type="password")
    
    # REQUIRE: ต้องกรอกครบ ปุ่มจึงจะ Unlock
    login_ready = u.strip() != "" and p.strip() != ""
    
    if st.button("Sign In", disabled=not login_ready):
        if u == "kittikoon.k@garena.com" and p == "garena123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("ข้อมูลไม่ถูกต้อง")
    
    if not login_ready:
        st.caption("🔒 โปรดระบุ Email และ Password เพื่อเข้าสู่ระบบ")

else:
    # --- 5. Main Application ---
    st.sidebar.title("💎 Menu")
    page = st.sidebar.radio("Navigate:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    if page == "PIC Workspace":
        st.title("📱 PIC Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('Gemini กำลังเรียก API...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res: st.session_state[f"res_{t['id']}"] = res

                if f"res_{t['id']}" in st.session_state:
                    for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                # REQUIRE: ต้องมี Draft ก่อนส่ง
                t['Draft'] = st.text_area("Final Draft (Require)", value=t['Draft'], key=f"ed_{t['id']}", height=100)
                
                if st.button("Submit (ส่งงาน)", key=f"sub_{t['id']}", disabled=not t['Draft'].strip()):
                    t['Status'] = "Done"
                    st.success("ส่งงานเรียบร้อย!")

    elif page == "Admin Control":
        st.title("👨‍💻 Admin")
        nt = st.text_input("Topic")
        ng = st.text_area("Guideline")
        # REQUIRE: ต้องกรอกครบ
        if st.button("Deploy Task", disabled=not (nt.strip() and ng.strip())):
            st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "Status": "Waiting", "Draft": ""})
            st.success("จ่ายงานสำเร็จ!")

    elif page == "Daily Report":
        st.title("📊 Report")
        st.table(pd.DataFrame(st.session_state.db))
