import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re

# ==========================================
# 1. การเชื่อมต่อ (เน้นความเสถียร)
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
                updated_values = [
                    str(task_data['id']), task_data.get('Topic', ''), task_data.get('PIC', ''), 
                    task_data.get('Status', ''), task_data.get('Guide', ''), task_data.get('Persona', ''), 
                    task_data.get('Draft', ''), task_data.get('Date', '')
                ]
                ws.update(f"A{cell.row}:H{cell.row}", [updated_values])
                return True
        except: pass
    return False

# ==========================================
# 2. AI CONNECTOR (แก้ไขจุดส่งค่าพลาด)
# ==========================================
def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ดึงค่าผ่าน str().strip() เพื่อป้องกันช่องว่างหรือค่า Null
    payload = {
        "inputs": {
            "Topic": str(topic).strip(),
            "Guide": str(guide).strip(),
            "Persona": str(persona).strip()
        },
        "response_mode": "blocking", 
        "user": "god_mode_admin"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # แกะเอาข้อความออกมา
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'outputs' in res:
            raw_text = res['outputs'].get('text', "")

        if not raw_text:
            return [f"⚠️ API Error: {res}"]

        # แยกเป็นข้อๆ 10 แบบ
        options = re.split(r'\n\s*\d+[\.\)]\s*|\n\s*-\s*', "\n" + str(raw_text).strip())
        return [opt.strip() for opt in options if len(opt.strip()) > 5]
    except Exception as e:
        return [f"❌ Fatal Error: {str(e)}"]

# ==========================================
# 3. UI (จุดที่ต้องแก้การส่งตัวแปร)
# ==========================================
st.set_page_config(page_title="RoV Seeding Pro", layout="wide")

# โหลดข้อมูล
if 'db' not in st.session_state:
    sh = init_connection()
    if sh:
        st.session_state.db = sh.worksheet("tasks").get_all_records()
        st.session_state.users_db = sh.worksheet("users").get_all_records()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# ส่วน Login (ข้ามไปส่วน Admin เลย)
if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    u_email = st.text_input("Email")
    u_pass = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user = next((x for x in st.session_state.users_db if x['email'] == u_email and str(x['password']) == u_pass), None)
        if user:
            st.session_state.logged_in, st.session_state.user_role, st.session_state.current_user = True, user['role'], user['email']
            st.rerun()
else:
    if st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

        for t in my_tasks:
            if t['Status'] != "Approved":
                with st.expander(f"📌 {t.get('Topic', 'No Topic')}", expanded=True):
                    
                    # หัวใจสำคัญ: การตั้ง Key และรับค่าจาก Widget โดยตรง
                    c1, c2, c3 = st.columns(3)
                    
                    # รับค่าจากช่องพิมพ์ด้วย key ที่ไม่ซ้ำกัน
                    current_topic = c1.text_input("แก้ไข Topic", value=t.get('Topic', ''), key=f"topic_input_{t['id']}")
                    current_guide = c2.text_area("แก้ไข Guide", value=t.get('Guide', ''), key=f"guide_input_{t['id']}")
                    current_persona = c3.text_area("แก้ไข Persona", value=t.get('Persona', ''), key=f"persona_input_{t['id']}")

                    # ปุ่ม Draft (ดึงตัวแปร current_xxx ไปส่งทันที)
                    if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_btn_{t['id']}", type="primary", use_container_width=True):
                        if not current_topic.strip():
                            st.error("แม่! ลืมพิมพ์หัวข้อหรือเปล่า? พิมพ์แล้วกด Enter ก่อนนะ")
                        else:
                            with st.spinner("AI กำลังรับข้อมูลที่คุณพิมพ์..."):
                                # ส่งค่า 'สดๆ' จาก Widget เข้าไปในฟังก์ชัน
                                results = call_ai_agent(current_topic, current_guide, current_persona)
                                st.session_state[f"temp_results_{t['id']}"] = results
                    
                    # แสดงผลลัพธ์
                    if f"temp_results_{t['id']}" in st.session_state:
                        st.markdown("---")
                        for i, msg in enumerate(st.session_state[f"temp_results_{t['id']}"]):
                            if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"sel_{t['id']}_{i}"):
                                t['Draft'] = msg
                                # เซฟค่าที่พิมพ์ลงไปด้วยกันหลุด
                                t['Topic'], t['Guide'], t['Persona'] = current_topic, current_guide, current_persona
                                update_task_in_sheets(t['id'], t)
                                st.rerun()

                    # ส่วนส่งงาน
                    t['Draft'] = st.text_area("ร่างสุดท้าย", value=t.get('Draft', ''), key=f"final_dr_{t['id']}")
                    if st.button("🚀 ส่งงาน (Review)", key=f"submit_{t['id']}", use_container_width=True):
                        t.update({'Topic': current_topic, 'Guide': current_guide, 'Persona': current_persona, 'Status': 'Reviewing'})
                        update_task_in_sheets(t['id'], t)
                        st.rerun()

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
