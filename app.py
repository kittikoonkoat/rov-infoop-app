import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re

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
        except: pass

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
# 2. AI CONNECTOR (WITH DEBUG LOG)
# ==========================================
def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ดึงค่าจากหน้าจอ ลบช่องว่างหัวท้าย
    payload = {
        "inputs": {
            "Topic": str(topic).strip(),
            "Guide": str(guide).strip(),
            "Persona": str(persona).strip()
        },
        "response_mode": "blocking", 
        "user": "admin_final"
    }
    
    try:
        # Debug: โชว์สิ่งที่ส่งไป (ลบออกได้ถ้าทำงานได้แล้ว)
        st.info(f"DEBUG SENDing: Topic={topic}")
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'outputs' in res:
            raw_text = res['outputs'].get('text', "")

        if not raw_text:
            return [f"❌ AI Error: {res}"]

        options = re.split(r'\n\s*\d+[\.\)]\s*|\n\s*-\s*', "\n" + str(raw_text).strip())
        return [opt.strip() for opt in options if len(opt.strip()) > 5]
    except Exception as e:
        return [f"❌ Connection Error: {str(e)}"]

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
    if st.button("Sign In"):
        if 'users_db' in st.session_state:
            user = next((x for x in st.session_state.users_db if x['email'] == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
else:
    if st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

        for t in my_tasks:
            if t['Status'] != "Approved":
                with st.expander(f"📌 {t.get('Topic', 'No Topic')}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    # ใช้ Key แยกกันเด็ดขาดเพื่อความแม่นยำ
                    in_t = c1.text_input("Topic", value=t.get('Topic', ''), key=f"it_{t['id']}")
                    in_g = c2.text_area("Guide", value=t.get('Guide', ''), key=f"ig_{t['id']}")
                    in_p = c3.text_area("Persona", value=t.get('Persona', ''), key=f"ip_{t['id']}")

                    if st.button("✨ Draft with AI", key=f"btn_{t['id']}", type="primary", use_container_width=True):
                        with st.spinner("กำลังปั่น..."):
                            results = call_ai_agent(in_t, in_g, in_p)
                            st.session_state[f"res_{t['id']}"] = results
                    
                    if f"res_{t['id']}" in st.session_state:
                        for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                            if st.button(f"เลือกแบบที่ {i+1}: {msg[:50]}...", key=f"s_{t['id']}_{i}"):
                                t['Draft'] = msg
                                t['Topic'], t['Guide'], t['Persona'] = in_t, in_g, in_p
                                update_task_in_sheets(t['id'], t)
                                st.rerun()

                    t['Draft'] = st.text_area("Draft", value=t.get('Draft', ''), key=f"d_{t['id']}")
                    if st.button("🚀 ส่งงาน", key=f"sub_{t['id']}"):
                        t.update({'Topic':in_t, 'Guide':in_g, 'Persona':in_p, 'Status':'Reviewing'})
                        update_task_in_sheets(t['id'], t)
                        st.rerun()

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
