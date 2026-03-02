import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
from datetime import datetime

# ==========================================
# 1. CORE CONNECTION
# ==========================================
def init_connection():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds).open("RoV_Seeding_DB")
    except:
        return None

def get_sheet_data(sheet_name):
    sh = init_connection()
    if sh:
        return sh.worksheet(sheet_name).get_all_records()
    return []

def update_task_in_sheets(task_id, task_data):
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet("tasks")
            cell = ws.find(str(task_id), in_column=1)
            if cell:
                updated_values = [
                    str(task_id), str(task_data.get('Topic', '')), str(task_data.get('PIC', '')), 
                    str(task_data.get('Status', '')), str(task_data.get('Guide', '')), 
                    str(task_data.get('Persona', '')), str(task_data.get('Draft', '')), 
                    str(task_data.get('Date', ''))
                ]
                ws.update(f"A{cell.row}:H{cell.row}", [updated_values])
                return True
        except: pass
    return False

# ==========================================
# 2. AI AGENT (INSEA CONNECTOR)
# ==========================================
def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": str(topic).strip(), "Guide": str(guide).strip(), "Persona": str(persona).strip()},
        "response_mode": "blocking", "user": "super_admin"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']: raw_text = res['data']['outputs'].get('text', "")
        elif 'outputs' in res: raw_text = res['outputs'].get('text', "")
        
        if not raw_text: return [f"⚠️ AI Error: {res}"]
        options = re.split(r'\n\s*\d+[\.\)]\s*|\n\s*-\s*', "\n" + str(raw_text).strip())
        return [opt.strip() for opt in options if len(opt.strip()) > 5]
    except Exception as e:
        return [f"❌ Error: {str(e)}"]

# ==========================================
# 3. PAGE FUNCTIONS
# ==========================================

def task_page():
    st.title("📥 My Assigned Tasks")
    tasks = get_sheet_data("tasks")
    my_tasks = [t for t in tasks if t['PIC'] == st.session_state.current_user]

    for t in my_tasks:
        if t['Status'] != "Approved":
            with st.expander(f"📌 {t.get('Topic', 'No Topic')} (สถานะ: {t['Status']})", expanded=True):
                c1, c2, c3 = st.columns(3)
                val_t = c1.text_input("Topic", value=t.get('Topic', ''), key=f"t_{t['id']}")
                val_g = c2.text_area("Guide", value=t.get('Guide', ''), key=f"g_{t['id']}")
                val_p = c3.text_area("Persona", value=t.get('Persona', ''), key=f"p_{t['id']}")

                if st.button("✨ Save & Draft with AI", key=f"ai_{t['id']}", type="primary", use_container_width=True):
                    t.update({'Topic': val_t, 'Guide': val_g, 'Persona': val_p})
                    with st.spinner("กำลังบันทึกและให้ AI ประมวลผล..."):
                        if update_task_in_sheets(t['id'], t):
                            results = call_ai_agent(val_t, val_g, val_p)
                            st.session_state[f"res_{t['id']}"] = results
                            st.rerun()

                if f"res_{t['id']}" in st.session_state:
                    st.write("---")
                    for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                        if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                            update_task_in_sheets(t['id'], t)
                            st.rerun()

                t['Draft'] = st.text_area("Draft สุดท้าย", value=t.get('Draft', ''), key=f"dr_{t['id']}")
                if st.button("🚀 ส่งงาน", key=f"sub_{t['id']}", use_container_width=True):
                    t.update({'Topic': val_t, 'Guide': val_g, 'Persona': val_p, 'Status': 'Reviewing'})
                    update_task_in_sheets(t['id'], t)
                    st.success("ส่งงานสำเร็จ!")
                    st.rerun()

def admin_mgmt_page():
    st.title("👤 Admin Management")
    users = get_sheet_data("users")
    st.table(pd.DataFrame(users))
    with st.expander("➕ เพิ่มแอดมินใหม่"):
        with st.form("add_user"):
            new_email = st.text_input("Email")
            new_pass = st.text_input("Password")
            new_role = st.selectbox("Role", ["Admin", "SuperAdmin"])
            if st.form_submit_button("บันทึก"):
                sh = init_connection()
                sh.worksheet("users").append_row([new_email, new_pass, new_role])
                st.success("เพิ่มสำเร็จ!")
                st.rerun()

def fb_group_page():
    st.title("👥 Facebook Group Management")
    groups = get_sheet_data("fb_groups")
    if groups: st.dataframe(pd.DataFrame(groups), use_container_width=True)
    with st.expander("➕ เพิ่มกลุ่มใหม่"):
        with st.form("add_group"):
            g_name = st.text_input("ชื่อกลุ่ม")
            g_url = st.text_input("URL")
            if st.form_submit_button("บันทึก"):
                sh = init_connection()
                sh.worksheet("fb_groups").append_row([g_name, g_url, "Active"])
                st.success("เพิ่มกลุ่มสำเร็จ!")
                st.rerun()

def performance_page():
    st.title("📈 Daily Performance")
    tasks = get_sheet_data("tasks")
    if tasks:
        df = pd.DataFrame(tasks)
        st.subheader("📊 สรุปสถานะงาน")
        status_count = df['Status'].value_counts()
        st.bar_chart(status_count)
        
        st.subheader("📄 รายละเอียดงานทั้งหมด")
        st.dataframe(df[['Date', 'Topic', 'PIC', 'Status']], use_container_width=True)

# ==========================================
# 4. MAIN NAVIGATION
# ==========================================
st.set_page_config(page_title="RoV Seeding Pro", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    with st.form("login_form"):
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            users = get_sheet_data("users")
            user = next((x for x in users if x['email'] == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in, st.session_state.current_user, st.session_state.user_role = True, user['email'], user['role']
                st.rerun()
            else: st.error("ข้อมูลไม่ถูกต้อง")
else:
    with st.sidebar:
        st.title(f"สวัสดี, {st.session_state.user_role}")
        menu = st.radio("เมนูหลัก", ["Tasks", "Admin Management", "FB Groups", "Performance"])
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.rerun()

    if menu == "Tasks": task_page()
    elif menu == "Admin Management": admin_mgmt_page()
    elif menu == "FB Groups": fb_group_page()
    elif menu == "Performance": performance_page()
