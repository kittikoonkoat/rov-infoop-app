import streamlit as st
import pandas as pd
import requests
import re

# --- UI Styling (Gemini Dark) ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")
st.markdown("<style>.stApp { background-color: #131314; color: #E3E3E3; }</style>", unsafe_allow_html=True)

def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run" 
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # ปรับ Payload ใหม่: 
    # บางครั้ง Insea API ต้องการให้ชื่อตัวแปรตรงเป๊ะกับใน Node (ลองเช็คในหน้า Workflow ว่าใช้ T ตัวใหญ่หรือเปล่านะครับ)
    payload = {
        "inputs": {
            "Topic": str(topic),
            "Guide": str(guide),
            "Persona": "กะเทย เล่น rov มานาน"
        },
        "response_mode": "blocking",
        "user": "gemini_final_fix"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # ถ้ารันแล้วยังได้ VALIDATION_VIOLATION ให้ลองเอา "inputs": { ... } ออกแล้วส่งแค่ { "Topic": ..., "response_mode": ... }
        if 'error' in res_data:
            st.error(f"❌ API ปฏิเสธข้อมูล: {res_data['error']['message']}")
            st.write("รายละเอียดที่ขาด:", res_data.get('fields'))
            return []

        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output:
            st.warning("⚠️ AI ตอบกลับมาแต่ไม่มีข้อความ (ตรวจสอบ LLM Node ใน Insea)")
            return []

        # ล้างสัญลักษณ์แปลกๆ
        clean_text = str(raw_output).replace('\\n', '\n')
        lines = [l.strip() for l in clean_text.split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
        
    except Exception as e:
        st.error(f"📡 เชื่อมต่อไม่สำเร็จ: {str(e)}")
        return []

# --- ส่วนแสดงผล PIC Workspace (ที่ต้องมี Validate) ---
if 'db' not in st.session_state:
    st.session_state.db = [{"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย", "Status": "Waiting", "Draft": ""}]

st.title("📱 RoV Seeding Portal")

for t in st.session_state.db:
    with st.expander(f"📌 {t['Topic']}", expanded=True):
        st.write(f"**Guide:** {t['Guide']}")
        
        if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
            # ตรวจสอบก่อนส่งว่ามีข้อมูลไหม
            if t['Topic'] and t['Guide']:
                with st.spinner('กำลังคุยกับ Insea API...'):
                    res = call_seeding_agent(t['Topic'], t['Guide'])
                    if res:
                        st.session_state[f"res_{t['id']}"] = res
            else:
                st.warning("กรุณากรอก Topic และ Guide ให้ครบก่อนสั่ง AI")

        if f"res_{t['id']}" in st.session_state:
            st.markdown("---")
            for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                st.info(msg)
                if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                    t['Draft'] = msg
        
        t['Draft'] = st.text_area("Final Draft (Require)", value=t['Draft'], key=f"ed_{t['id']}")
        
        # Validate: ต้องกรอกร่างสุดท้ายก่อนส่ง
        if st.button("Submit", key=f"sub_{t['id']}", disabled=not t['Draft'].strip()):
            st.balloons()
            st.success("ส่งงานสำเร็จ!")
