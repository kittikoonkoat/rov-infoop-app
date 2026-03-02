import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. GOOGLE SHEETS CONNECTION & DATABASE
# ==========================================

def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"❌ การเชื่อมต่อ Sheets ล้มเหลว: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.sidebar.success("🔄 ซิงค์ข้อมูลล่าสุดแล้ว")
        except Exception as e:
            st.error(f"ไม่พบหน้าข้อมูล: {e}")

def add_new_task(new_task):
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet("tasks")
            ws.append_row(list(new_task.values())) # เพิ่มแถวใหม่ต่อท้าย
            return True
        except Exception as e:
            st.error(f"เพิ่มงานไม่สำเร็จ: {e}")
    return False

def update_task_in_sheets(task_id, task_data):
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet("tasks")
            # หาแถวที่มี ID ตรงกันในคอลัมน์ A
            cell = ws.find(str(task_id), in_column=1)
            if cell:
                row_idx = cell.row
                # ลำดับต้องตรงกับหัวตาราง: id, Topic, PIC, Status, Guide, Persona, Draft, Date
                updated_values = [
                    str(task_data['id']), task_data['Topic'], task_data['PIC'], 
                    task_data['Status'], task_data['Guide'], task_data['Persona'], 
                    task_data['Draft'], task_data['Date']
                ]
                ws.update(f"A{row_idx}:H{row_idx}", [updated_values]) # อัปเดตเฉพาะแถว
                return True
        except Exception as e:
            st.error(f"อัปเดตงานล้มเหลว: {e}")
    return False

# ==========================================
# 2. AI WORKFLOW CONNECTOR (Robust Version)
# ==========================================

def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "inputs": {"Topic": str(topic), "Guide": str(guide), "Persona": str(persona)},
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # ดึงข้อความดิบออกมา
        raw_text = res.get('data', {}).get('outputs', {}).get('text', "").strip()
        
        if not raw_text:
            return ["❌ AI ไม่ตอบกลับมา ลองตรวจสอบ Prompt อีกครั้ง"]

        # แยกข้อความ 1. หรือ - หรือตัวเลขอื่นๆ
        options = re.split(r'\n\d+[\.\)]\s*|\n-\s*', "\n" + raw_text)
        clean_options = [opt.strip() for opt in options if len(opt.strip()) > 5]
        
        # Fallback: ถ้าแยกไม่ได้เลย ให้เอาข้อความทั้งหมดมาเป็นตัวเลือกเดียว
        if not clean_options and len(raw_text) > 0:
            clean_options = [raw_text]
            
        return clean_options[:10]
    except Exception as e:
        return [f"❌ AI Error: {str(e)}"]

# ==========================================
# 3. UI APPLICATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN PAGE ---
if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    col_login, _ = st.columns([1, 2])
    with col_login:
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            user = next((x for x in st.session_state.users_db if x['email'] == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

# --- MAIN APP ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    st.sidebar.write(st.session_state.current_user)

    # 👨‍💼 BOSS ROLE
    if st.session_state.user_role == "Boss":
        st.title("👨‍💼 Boss Assignment & Review")
        
        with st.expander("➕ สั่งงาน Seeding ใหม่", expanded=False):
            with st.form("add_task"):
                topic = st.text_input("หัวข้อคอนเทนต์ (Topic):")
                pic = st.selectbox("เลือก Admin:", [u['email'] for u in st.session_state.users_db if u['role'] == 'Admin'])
                if st.form_submit_button("ส่งงาน"):
                    # ใช้ Unique ID อิงจากเวลา
                    task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    new_task = {
                        "id": task_id, "Topic": topic, "PIC": pic, "Status": "Pending",
                        "Guide": "", "Persona": "แอดมินกะเทย RoV", "Draft": "", "Date": str(datetime.date.today())
                    }
                    if add_new_task(new_task):
                        st.success("ส่งงานสำเร็จ!")
                        sync_data()
                        st.rerun()

        st.subheader("🔍 งานที่รอการอนุมัติ")
        review_tasks = [t for t in st.session_state.db if t['Status'] == "Reviewing"]
        
        if not review_tasks:
            st.info("ยังไม่มีงานรอตรวจ")

        for t in review_tasks:
            with st.expander(f"📋 ตรวจงาน: {t['Topic']} (โดย {t['PIC']})", expanded=True):
                st.write(f"**Guide:** {t['Guide']} | **Persona:** {t['Persona']}")
                st.info(f"**ร่างข้อความ:** \n\n {t['Draft']}")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"app_{t['id']}", use_container_width=True):
                    t['Status'] = "Approved"
                    update_task_in_sheets(t['id'], t)
                    st.rerun()
                if c2.button("❌ Reject", key=f"rej_{t['id']}", use_container_width=True):
                    t['Status'] = "Pending"
                    update_task_in_sheets(t['id'], t)
                    st.rerun()

    # 📥 ADMIN ROLE
    elif st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

        for t in my_tasks:
            if t['Status'] != "Approved":
                with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                    col1, col2 = st.columns(2)
                    # ดึงค่าจากตัวแปร t มาใส่ใน text_area
                    t['Guide'] = col1.text_area("แนวทาง (Guide):", value=t['Guide'], key=f"g_{t['id']}")
                    t['Persona'] = col2.text_area("บุคลิก AI (Persona):", value=t['Persona'], key=f"p_{t['id']}")

                    if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_{t['id']}"):
                        with st.spinner("กำลังปั่นเนื้อหา..."):
                            st.session_state[f"opts_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'], t['Persona'])
                    
                    if f"opts_{t['id']}" in st.session_state:
                        st.markdown("---")
                        for i, msg in enumerate(st.session_state[f"opts_{t['id']}"]):
                            if st.button(f"เลือกแบบที่ {i+1}: {msg[:70]}...", key=f"sel_{t['id']}_{i}", use_container_width=True):
                                t['Draft'] = msg
                                update_task_in_sheets(t['id'], t) # บันทึกร่างทันทีกันหาย
                                st.rerun()

                    t['Draft'] = st.text_area("ร่างข้อความสุดท้าย (แก้ไขเพิ่มได้):", value=t['Draft'], key=f"dr_{t['id']}", height=150)
                    
                    if st.button("🚀 ส่งให้ Boss ตรวจ", key=f"sub_{t['id']}", type="primary", use_container_width=True):
                        t['Status'] = "Reviewing"
                        update_task_in_sheets(t['id'], t)
                        st.success("ส่งงานเรียบร้อย!")
                        st.rerun()
            else:
                st.success(f"✅ งาน '{t['Topic']}' ได้รับการอนุมัติแล้ว")

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
