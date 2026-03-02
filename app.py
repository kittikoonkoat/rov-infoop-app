import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. CONNECTION & SYNC
# ==========================================

def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds).open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"❌ เชื่อมต่อ Sheets ไม่ได้: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
        except Exception as e:
            st.error(f"Sync Error: {e}")

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
        except Exception as e:
            st.error(f"Update Error: {e}")
    return False

# ==========================================
# 2. AI CONNECTOR (FIXED MAPPING FOR START NODE)
# ==========================================

def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ดึงค่าและจัดการค่าว่างให้มีเนื้อหาขั้นต่ำ
    s_topic = str(topic).strip() if topic else "ทั่วไป"
    s_guide = str(guide).strip() if guide else "คอมเมนต์ให้น่าสนใจ"
    s_persona = str(persona).strip() if persona else "กะเทยเล่น RoV"

    # Payload ต้องมี KEY ตรงกับใน Start Node ของ Insea (Case-sensitive)
    payload = {
        "inputs": {
            "Topic": s_topic,   # ต้องขึ้นต้นด้วย T ตัวใหญ่ตามภาพ Start Node
            "Guide": s_guide,   # ต้องขึ้นต้นด้วย G ตัวใหญ่
            "Persona": s_persona # ต้องขึ้นต้นด้วย P ตัวใหญ่
        },
        "response_mode": "blocking", 
        "user": "admin_portal"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            return [f"❌ API Error {response.status_code}: {response.text[:100]}"]
            
        res = response.json()
        
        # ค้นหาข้อความคำตอบจากโครงสร้าง JSON ของ Insea
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'outputs' in res:
            raw_text = res['outputs'].get('text', "")

        # หากได้ข้อความ แต่สั้นเกินไป หรือ AI ตอบกวนว่าไม่มีหัวข้อ
        if not raw_text or len(str(raw_text).strip()) < 5:
            return [f"⚠️ AI ไม่ยอมตอบเนื้อหา: {res.get('message', 'ลองตรวจสอบ Prompt ใน Insea ว่าได้ใส่ตัวแปร {Topic} หรือยัง')}"]

        # แยกข้อความ 10 แบบ (รองรับทั้งแบบตัวเลข 1. และแบบขีด -)
        options = re.split(r'\n\s*\d+[\.\)]\s*|\n\s*-\s*', "\n" + str(raw_text).strip())
        clean_options = [opt.strip() for opt in options if len(opt.strip()) > 5]
        
        return clean_options if clean_options else [str(raw_text)]
        
    except Exception as e:
        return [f"❌ Error Connect: {str(e)}"]

# ==========================================
# 3. UI APPLICATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state: sync_data()
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    u_email = st.text_input("Email")
    u_pass = st.text_input("Password", type="password")
    if st.button("Sign In", use_container_width=True):
        if 'users_db' in st.session_state:
            user = next((x for x in st.session_state.users_db if x['email'] == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
else:
    if st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

        for t in my_tasks:
            if t['Status'] != "Approved":
                # แสดงชื่อหัวข้อที่ Boss สั่งมาในแถบ Expander
                with st.expander(f"📌 {t.get('Topic', 'No Topic')} | สถานะ: {t.get('Status', 'Pending')}", expanded=True):
                    st.markdown("### 📝 รายละเอียดงาน")
                    
                    col_t, col_g, col_p = st.columns([1, 1, 1])
                    
                    # ช่องกรอกข้อมูลที่ AI จะอ่าน (หัวข้อ/แนวทาง/บุคลิก)
                    # แก้ไขให้ Topic แสดงค่าจากที่ Boss พิมพ์มาเป็นค่าเริ่มต้น
                    input_topic = col_t.text_input("หัวข้อคอนเทนต์ (Topic):", value=t.get('Topic', ''), key=f"t_{t['id']}")
                    input_guide = col_g.text_area("แนวทาง (Guide):", value=t.get('Guide', ''), key=f"g_{t['id']}", height=100)
                    input_persona = col_p.text_area("บุคลิก AI (Persona):", value=t.get('Persona', ''), key=f"p_{t['id']}", height=100)

                    if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_{t['id']}", type="primary", use_container_width=True):
                        if not input_topic:
                            st.warning("⚠️ แม่! ลืมใส่หัวข้อคอนเทนต์ AI ไปไม่เป็นเลยนะ!")
                        else:
                            with st.spinner("AI กำลังปั่นเนื้อหา..."):
                                # ส่งค่าจากหน้าจอ (input_topic) ไม่ใช่จาก DB (t['Topic']) เพื่อความสดใหม่
                                results = call_ai_agent(input_topic, input_guide, input_persona)
                                st.session_state[f"opts_{t['id']}"] = results
                    
                    # ส่วนแสดงผลลัพธ์จาก AI
                    if f"opts_{t['id']}" in st.session_state:
                        st.markdown("---")
                        st.subheader("เลือกร่างที่ชอบ:")
                        for i, msg in enumerate(st.session_state[f"opts_{t['id']}"]):
                            if st.button(f"เลือกแบบที่ {i+1}: {msg[:80]}...", key=f"sel_{t['id']}_{i}", use_container_width=True):
                                t['Draft'] = msg
                                t['Topic'] = input_topic # บันทึกหัวข้อที่แก้ไขแล้วลงไปด้วย
                                if update_task_in_sheets(t['id'], t):
                                    st.success("บันทึกร่างเรียบร้อย!")
                                    st.rerun()

                    t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t.get('Draft', ''), key=f"dr_{t['id']}", height=150)
                    if st.button("🚀 ส่งงานให้ Boss", key=f"sub_{t['id']}", use_container_width=True):
                        t['Status'] = "Reviewing"
                        if update_task_in_sheets(t['id'], t):
                            st.rerun()

    elif st.session_state.user_role == "Boss":
        # ... (โค้ดส่วน Boss เหมือนเดิม) ...
        st.title("👨‍💼 Review Board")
        # โค้ดส่วนแสดงงานที่รอตรวจ
        pass

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
