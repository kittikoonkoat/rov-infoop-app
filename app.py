import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling: Ultra Clean Gemini Dark ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; }
    /* ปรับแต่งปุ่มให้ดูแพง */
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; border: none; padding: 0.6rem 2.5rem; font-weight: 500;
    }
    /* สไตล์ปุ่มเมื่อถูกล็อค (Disabled) */
    div.stButton > button:disabled {
        background: #333537 !important; color: #757575 !important; cursor: not-allowed; border: 1px solid #444746 !important;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1E1F20 !important; color: #FFFFFF !important;
        border: 1px solid #444746 !important; border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize DB & State ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Status": "Waiting", "Draft": ""}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. API Connector: Fixed for 'message is empty' ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ส่งข้อมูลกลับเข้าโครงสร้าง inputs แต่ส่งแบบ Explicit String
    payload = {
        "inputs": {
            "Topic": str(topic),
            "Guide": str(guide),
            "Persona": "กะเทย เล่น rov มานาน"
        },
        "response_mode": "blocking",
        "user": "gemini_final_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # เช็ค Error จาก API
        if 'error' in res_data:
            st.error(f"❌ API ปฏิเสธ: {res_data['error'].get('message', 'Unknown Error')}")
            return []

        # ดึงข้อมูลจาก Data Path
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output:
            st.warning("⚠️ AI ยังไม่ส่งข้อมูล (ลองเช็ค Node LLM ใน Insea ว่าเชื่อมกับ Output หรือยัง)")
            return []

        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except Exception as e:
        st.error(f"📡 Connection Error: {str(e)}")
        return []

# --- 4. Login Screen: Requirement Validation ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    with st.container():
        u = st.text_input("Garena Email", placeholder="kittikoon.k@garena.com")
        p = st.text_input("Password", type="password")
        
        # REQUIRE: ต้องกรอกครบทั้งคู่ ปุ่มถึงจะหายเป็นสีเทา
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
    # --- 5. Main Application ---
    st.sidebar.title(f"💎 คุณกิตติคุณ")
    page = st.sidebar.radio("เมนู:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- PIC Workspace (Strict Edit Mode) ---
    if page == "PIC Workspace":
        st.title("📱 PIC Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**แนวทาง:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('กำลังรอ AI ร่างข้อความ...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res: st.session_state[f"res_{t['id']}"] = res

                if f"res_{t['id']}" in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                # REQUIRE: ช่อง Final Draft ต้องไม่ว่าง
                t['Draft'] = st.text_area("Final Draft (Require)", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                
                can_submit = t['Draft'].strip() != ""
                if st.button("ยืนยันการส่ง (Submit)", key=f"sub_{t['id']}", disabled=not can_submit):
                    t['Status'] = "Done"
                    st.success("ส่งงานสำเร็จ!")
                elif not can_submit:
                    st.caption("⚠️ โปรดร่างข้อความให้เรียบร้อยก่อนกด Submit")

    # --- Admin Control (Strict Add Mode) ---
    elif page == "Admin Control":
        st.title("👨‍💻 Admin Control")
        nt = st.text_input("หัวข้อ (Topic)")
        ng = st.text_area("แนวทาง (Guideline)")
        
        # REQUIRE: ต้องกรอกครบทุกช่องปุ่มถึงจะทำงาน
        admin_ready = nt.strip() != "" and ng.strip() != ""
        
        if st.button("Deploy Task", disabled=not admin_ready):
            st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "Status": "Waiting", "Draft": ""})
            st.success(f"จ่ายงาน '{nt}' เรียบร้อย!")
        
        if not admin_ready:
            st.info("💡 กรุณากรอกทั้งหัวข้อและแนวทางเพื่อปลดล็อคปุ่ม Deploy")

    # --- Daily Report ---
    elif page == "Daily Report":
        st.title("📊 Report")
        if st.session_state.db:
            st.table(pd.DataFrame(st.session_state.db))
