import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re

# ==========================================
# 1. การเชื่อมต่อ & ฟังก์ชันพื้นฐาน
# ==========================================
def init_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds).open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None

def update_task_in_sheets(task_id, task_data):
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet("tasks")
            cell = ws.find(str(task_id), in_column=1)
            if cell:
                # บันทึกข้อมูลทั้งหมดลงไปใน Sheet ก่อน
                updated_values = [
                    str(task_id), 
                    str(task_data.get('Topic', '')), 
                    str(task_data.get('PIC', '')), 
                    str(task_data.get('Status', '')), 
                    str(task_data.get('Guide', '')), 
                    str(task_data.get('Persona', '')), 
                    str(task_data.get('Draft', '')), 
                    str(task_data.get('Date', ''))
                ]
                ws.update(f"A{cell.row}:H{cell.row}", [updated_values])
                return True
        except Exception as e:
            st.error(f"Update Error: {e}")
    return False

# ==========================================
# 2. AI CONNECTOR
# ==========================================
def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "inputs": {
            "Topic": str(topic).strip(),
            "Guide": str(guide).strip(),
            "Persona": str(persona).strip()
        },
        "response_mode": "blocking", 
        "user": "admin_system"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'outputs' in res:
            raw_text = res['outputs'].get('text', "")

        if not raw_text:
            return [f"⚠️ AI Error: {res}"]

        options = re.split(r'\n\s*\d+[\.\)]\s*|\n\s*-\s*', "\n" + str(raw_text).strip())
        return [opt.strip() for opt in options if len(opt.strip()) > 5]
    except Exception as e:
        return [f"❌ Connection Error: {str(e)}"]

# ==========================================
# 3. UI APPLICATION (STRATEGY: SAVE THEN AI)
# ==========================================
st.set_page_config(page_title="RoV Seeding Pro", layout="wide")

# โหลดข้อมูลเข้า Session
if 'db' not in st.session_state:
    sh = init_connection()
    if sh:
        st.session_state.db = sh.worksheet("tasks").get_all_records()
        st.session_state.users_db = sh.worksheet("users").get_all_records()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# (ส่วน Login ตัดมาที่หน้า Admin เลย)
if st.session_state.logged_in and st.session_state.user_role == "Admin":
    st.title("📥 My Assigned Tasks")
    my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

    for t in my_tasks:
        if t['Status'] != "Approved":
            with st.expander(f"📌 {t.get('Topic', 'No Topic')}", expanded=True):
                c1, c2, c3 = st.columns(3)
                
                # Input Widgets
                new_topic = c1.text_input("Topic", value=t.get('Topic', ''), key=f"t_{t['id']}")
                new_guide = c2.text_area("Guide", value=t.get('Guide', ''), key=f"g_{t['id']}")
                new_persona = c3.text_area("Persona", value=t.get('Persona', ''), key=f"p_{t['id']}")

                # --- NEW LOGIC: SAVE THEN DRAFT ---
                if st.button("✨ Save & Generate AI", key=f"btn_{t['id']}", type="primary", use_container_width=True):
                    if not new_topic.strip():
                        st.warning("กรุณากรอก Topic ก่อนครับ")
                    else:
                        with st.spinner("Step 1: กำลังบันทึกข้อมูลลงฐานข้อมูล..."):
                            # อัปเดตข้อมูลในตัวแปร t
                            t['Topic'] = new_topic
                            t['Guide'] = new_guide
                            t['Persona'] = new_persona
                            
                            # บันทึกลง Google Sheets ทันที
                            success = update_task_in_sheets(t['id'], t)
                        
                        if success:
                            with st.spinner("Step 2: ข้อมูลพร้อมแล้ว! AI กำลังประมวลผล..."):
                                # ส่งค่าที่เพิ่งบันทึกสำเร็จไปให้ AI
                                results = call_ai_agent(new_topic, new_guide, new_persona)
                                st.session_state[f"res_{t['id']}"] = results
                                st.success("บันทึกข้อมูลและ Generate สำเร็จ!")
                        else:
                            st.error("เกิดข้อผิดพลาดในการบันทึกข้อมูลลง Sheets")

                # แสดงผลลัพธ์จาก AI
                if f"res_{t['id']}" in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                        if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                            update_task_in_sheets(t['id'], t)
                            st.rerun()

                t['Draft'] = st.text_area("Draft สุดท้าย", value=t.get('Draft', ''), key=f"dr_{t['id']}")
                if st.button("🚀 ส่งงาน (Review)", key=f"sub_{t['id']}", use_container_width=True):
                    t['Status'] = 'Reviewing'
                    t['Topic'], t['Guide'], t['Persona'] = new_topic, new_guide, new_persona
                    update_task_in_sheets(t['id'], t)
                    st.rerun()
else:
    # (โค้ดส่วน Login ปกติ)
    st.write("Please Sign In")
