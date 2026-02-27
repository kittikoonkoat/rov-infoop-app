import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling: Ultra Clean ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; border-right: 1px solid #333537; }
    .stTextInput input, .stTextArea textarea {
        background-color: #1E1F20 !important; color: #FFFFFF !important;
        border: 1px solid #444746 !important; border-radius: 12px !important;
    }
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; border: none; padding: 0.6rem 2.5rem; font-weight: 500;
    }
    /* ปรับสีปุ่มเมื่อถูกล็อค (Disabled) */
    div.stButton > button:disabled {
        background: #333537 !important; color: #757575 !important; cursor: not-allowed; border: 1px solid #444746 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize DB & State ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Status": "Waiting", "Draft": ""}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. API Connector (ใช้ API URL สำหรับเชื่อมต่อ) ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run" 
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": "กะเทย เล่น rov มานาน"},
        "response_mode": "blocking",
        "user": "gemini_fixed"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        if not raw_output: return []
        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except:
        return []

# --- 4. Login Screen (Fixed Button Lock) ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    # เปลี่ยนมาใช้การเช็คค่าแบบ Real-time นอก Form เพื่อแก้ปัญหาปุ่มกดไม่ได้
    u = st.text_input("Garena Email", placeholder="kittikoon.k@garena.com")
    p = st.text_input("Password", type="password")
    
    # REQUIRE: ต้องกรอกครบทั้ง Email และ Password
    login_ready = len(u.strip()) > 0 and len(p.strip()) > 0
    
    if st.button("Sign In", disabled=not login_ready):
        if u == "kittikoon.k@garena.com" and p == "garena123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("ข้อมูล Login ไม่ถูกต้องครับ")
    
    if not login_ready:
        st.caption("🔒 โปรดกรอกข้อมูลให้ครบเพื่อเปิดใช้งานปุ่ม Sign In")

else:
    # --- 5. Main Application Logic ---
    st.sidebar.title("💎 Navigation")
    page = st.sidebar.radio("Go to:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- PIC Workspace ---
    if page == "PIC Workspace":
        st.title("📱 PIC Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('AI กำลังร่างข้อความ...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res: st.session_state[f"res_{t['id']}"] = res
                        else: st.error("AI ไม่ตอบกลับ (เช็คปุ่ม Publish ใน Insea)")

                # แก้ไขปัญหา Syntax Error ตรงนี้ให้สมบูรณ์
                res_key = f"res_{t['id']}"
                if res_key in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[res_key]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                # REQUIRE: ต้องกรอกช่องร่างข้อความก่อนส่ง
                t['Draft'] = st.text_area("Final Draft (Require)", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                
                submit_active = len(t['Draft'].strip()) > 0
                if st.button("Submit (ส่งงาน)", key=f"sub_{t['id']}", disabled=not submit_active):
                    t['Status'] = "Done"
                    st.success("ส่งงานสำเร็จ!")
                elif not submit_active:
                    st.caption("⚠️ โปรดกรอกข้อความในช่อง Final Draft ก่อนกดส่งงาน")

    # --- Admin Control ---
    elif page == "Admin Control":
        st.title("👨‍💻 Admin Control")
        nt = st.text_input("หัวข้อ (Topic)")
        ng = st.text_area("แนวทาง (Guideline)")
        
        # REQUIRE: ต้องกรอกครบทุกช่อง
        add_ready = len(nt.strip()) > 0 and len(ng.strip()) > 0
        
        if st.button("Deploy Task", disabled=not add_ready):
            st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "Status": "Waiting", "Draft": ""})
            st.success(f"เพิ่มงานหัวข้อ '{nt}' สำเร็จ")
        
        if not add_ready:
            st.info("💡 โปรดกรอกทั้งหัวข้อและแนวทางเพื่อปลดล็อคปุ่ม")

    # --- Daily Report ---
    elif page == "Daily Report":
        st.title("📊 Report Summary")
        if st.session_state.db:
            st.table(pd.DataFrame(st.session_state.db))
