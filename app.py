import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling: Gemini Dark Aesthetic ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; }
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; border: none; padding: 0.6rem 2.5rem; font-weight: 500;
    }
    div.stButton > button:disabled {
        background: #333537 !important; color: #757575 !important; cursor: not-allowed; border: 1px solid #444746 !important;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1E1F20 !important; color: #FFFFFF !important;
        border: 1px solid #444746 !important; border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Initialize Session State ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ ลูกรักคนใหม่", "Status": "Waiting", "Draft": ""}]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. API Connector (Fixed Flatten Structure) ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ส่งแบบ Flat เพื่อเลี่ยง Validation Error
    payload = {
        "Topic": str(topic),
        "Guide": str(guide),
        "Persona": "กะเทย เล่น rov มานาน",
        "response_mode": "blocking",
        "user": "gemini_final_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        if 'error' in res_data:
            st.error(f"❌ API Error: {res_data['error'].get('message')}")
            return []

        # ดึงข้อมูลจาก Node End
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        if not raw_output:
            raw_output = res_data.get('text', "") 

        if not raw_output:
            st.warning("⚠️ AI ส่งค่าว่างกลับมา (ตรวจสอบช่อง User ใน Insea และกด Publish ด้วยนะครับ)")
            return []

        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except Exception as e:
        st.error(f"📡 Connection Error: {str(e)}")
        return []

# --- 4. Login Logic (Strict Requirement) ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    u = st.text_input("Garena Email")
    p = st.text_input("Password", type="password")
    
    # REQUIRE: ต้องกรอกครบถึงจะกดได้
    login_ready = u.strip() != "" and p.strip() != ""
    
    if st.button("Sign In", disabled=not login_ready):
        if u == "kittikoon.k@garena.com" and p == "garena123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
else:
    # --- 5. Application Main Workspace ---
    st.sidebar.title(f"💎 ยินดีต้อนรับ")
    page = st.sidebar.radio("เมนูใช้งาน:", ["PIC Workspace", "Admin Control", "Daily Report"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    if page == "PIC Workspace":
        st.title("📱 PIC Workspace")
        for t in st.session_state.db:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                # ปุ่ม AI Draft
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('Gemini กำลังเรียก Insea...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res:
                            st.session_state[f"res_list_{t['id']}"] = res

                # แสดงตัวเลือก AI และระบบการกดเลือก (Selection System)
                if f"res_list_{t['id']}" in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[f"res_list_{t['id']}"]):
                        col1, col2 = st.columns([0.85, 0.15])
                        with col1:
                            st.info(msg)
                        with col2:
                            # เมื่อกดเลือก จะนำค่าไปใส่ใน session_state ของช่อง text_area ทันที
                            if st.button(f"เลือก ✅", key=f"btn_{t['id']}_{i}"):
                                st.session_state[f"ed_{t['id']}"] = msg
                                t['Draft'] = msg
                                st.rerun()

                # ช่อง Final Draft ที่เชื่อมกับ session_state
                t['Draft'] = st.text_area(
                    "Final Draft (Require)", 
                    key=f"ed_{t['id']}", 
                    height=150,
                    placeholder="เลือกจาก AI ด้านบน หรือพิมพ์เองที่นี่..."
                )
                
                # REQUIRE: ต้องมีข้อความก่อนกดส่ง
                can_submit = t['Draft'].strip() != ""
                if st.button("Submit (ส่งงาน)", key=f"sub_{t['id']}", disabled=not can_submit):
                    t['Status'] = "Done"
                    st.balloons()
                    st.success("ส่งงานสำเร็จ!")

    elif page == "Admin Control":
        st.title("👨‍💻 Admin Control")
        nt = st.text_input("หัวข้อใหม่ (Topic)")
        ng = st.text_area("แนวทาง (Guideline)")
        # REQUIRE: แอดมินต้องกรอกครบ
        admin_ready = nt.strip() != "" and ng.strip() != ""
        if st.button("Deploy Task", disabled=not admin_ready):
            st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "Status": "Waiting", "Draft": ""})
            st.success("Deploy สำเร็จ!")

    elif page == "Daily Report":
        st.title("📊 Report Summary")
        st.table(pd.DataFrame(st.session_state.db))
