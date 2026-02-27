import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")
st.markdown("<style>.stApp { background-color: #131314; color: #E3E3E3; }</style>", unsafe_allow_html=True)

# --- 2. API Connector (พร้อมระบบตรวจสอบ Error) ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run" 
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": "กะเทย เล่น rov มานาน"},
        "response_mode": "blocking",
        "user": "gemini_debug"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # DEBUG: ถ้าพัง ให้โชว์ก้อนข้อมูลที่ API ส่งมาเลย
        if 'data' not in res_data:
            st.error(f"โครงสร้าง API ผิดพลาด: {res_data}")
            return []

        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output:
            st.warning("⚠️ AI ตอบกลับมาเป็นค่าว่าง (ตรวจสอบการเชื่อม Node ใน Insea)")
            return []

        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except Exception as e:
        st.error(f"การเชื่อมต่อล้มเหลว: {str(e)}")
        return []

# --- 3. Main Logic (Strict Validation) ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย", "Status": "Waiting", "Draft": ""}]

st.title("📱 RoV Seeding Portal")

for t in st.session_state.db:
    with st.expander(f"📌 {t['Topic']}", expanded=True):
        st.write(f"**Guide:** {t['Guide']}")
        
        # ปุ่ม Draft (ต้องกดได้เสมอเพื่อดึงข้อมูล)
        if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
            with st.spinner('กำลังดึงข้อมูล...'):
                res = call_seeding_agent(t['Topic'], t['Guide'])
                if res:
                    st.session_state[f"res_{t['id']}"] = res

        # แสดงผลลัพธ์
        if f"res_{t['id']}" in st.session_state:
            for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                st.info(msg)
                if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                    t['Draft'] = msg
        
        t['Draft'] = st.text_area("Final Draft (Require)", value=t['Draft'], key=f"ed_{t['id']}")
        
        # REQUIRE: ต้องกรอกให้ครบทุกช่องจึงจะกด Submit ได้
        can_submit = len(t['Draft'].strip()) > 0
        if st.button("Submit", key=f"sub_{t['id']}", disabled=not can_submit):
            st.success("ส่งงานสำเร็จ!")
