import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. GOOGLE SHEETS CONNECTION
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
        st.error(f"❌ การเชื่อมต่อล้มเหลว: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.sidebar.success("🔄 ข้อมูลซิงค์สำเร็จ")
        except Exception as e:
            st.error(f"ไม่พบหน้าข้อมูล: {e}")

def save_to_sheets(data_list):
    sh = init_connection()
    if sh:
        ws = sh.worksheet("tasks")
        ws.clear()
        df = pd.DataFrame(data_list)
        ws.update([df.columns.values.tolist()] + df.values.tolist())

# ==========================================
# 2. AI WORKFLOW CONNECTOR (3 Inputs)
# ==========================================

def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": str(persona)
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        options = [l.strip() for l in re.split(r'\n|\d+\.', str(raw_text)) if len(l.strip()) > 5]
        return options[:10] if options else ["AI คิดไม่ออก ลองปรับ Guide/Persona นะคะ"]
    except Exception as e:
        return [f"❌ Error AI: {str(e)}"]

# ==========================================
# 3. UI APPLICATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    u_email = st.text_input("Email")
    u_pass = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user = next((x for x in st.session_state.users_db if x['email'] == u_email and str(x['password']) == u_pass), None)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_role = user['role']
            st.session_state.current_user = user['email']
            st.rerun()
        else:
            st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

else:
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    st.sidebar.write(st.session_state.current_user)

    # 1. หน้าจอสำหรับ BOSS (สั่งงาน & อนุมัติงาน)
    if st.session_state.user_role == "Boss":
        st.title("👨‍💼 Boss Assignment & Review")
        
        # ส่วนที่ 1: สั่งงานใหม่
        with st.expander("➕ สั่งงาน Seeding ใหม่"):
            with st.form("add_task"):
                topic = st.text_input("หัวข้อคอนเทนต์ (Topic):")
                pic = st.selectbox("เลือก Admin:", [u['email'] for u in st.session_state.users_db if u['role'] == 'Admin'])
                if st.form_submit_button("ส่งงาน"):
                    new_task = {
                        "id": len(st.session_state.db) + 1, "Topic": topic, "PIC": pic, "Status": "Pending",
                        "Guide": "", "Persona": "", "Draft": "", "Date": str(datetime.date.today())
                    }
                    st.session_state.db.append(new_task)
                    save_to_sheets(st.session_state.db)
                    st.success("ส่งงานสำเร็จ!")
                    st.rerun()

        # ส่วนที่ 2: ตรวจสอบงานที่ Admin ส่งมา
        st.subheader("🔍 งานที่รอการอนุมัติ")
        review_tasks = [t for t in st.session_state.db if t['Status'] == "Reviewing"]
        
        if not review_tasks:
            st.write("ยังไม่มีงานที่รอตรวจในขณะนี้")
        
        for t in review_tasks:
            with st.expander(f"📋 ตรวจงาน: {t['Topic']} (โดย {t['PIC']})", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                st.write(f"**Persona:** {t['Persona']}")
                st.info(f"**ข้อความร่าง:** \n\n {t['Draft']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ อนุมัติ (Approve)", key=f"app_{t['id']}", use_container_width=True):
                        t['Status'] = "Approved"
                        save_to_sheets(st.session_state.db)
                        st.success("อนุมัติงานแล้ว!")
                        st.rerun()
                with col2:
                    if st.button("❌ ตีกลับ (Reject)", key=f"rej_{t['id']}", use_container_width=True):
                        t['Status'] = "Pending"
                        save_to_sheets(st.session_state.db)
                        st.warning("ตีกลับงานให้แก้ไข")
                        st.rerun()

    # 2. หน้าจอสำหรับ ADMIN (ใส่ Guide, Persona และเรียก AI)
    elif st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

        for t in my_tasks:
            # เฉพาะงานที่ยังไม่ผ่าน Approve
            if t['Status'] != "Approved":
                with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                    st.info(f"**Topic จาก Boss:** {t['Topic']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        t['Guide'] = st.text_area("แนวทาง (Guide):", value=t['Guide'], key=f"g_{t['id']}")
                    with col2:
                        t['Persona'] = st.text_area("บุคลิก AI (Persona):", value=t['Persona'] if t['Persona'] else "แอดมินกะเทย RoV", key=f"p_{t['id']}")

                    if st.button("✨ Draft with AI (10 แบบ)", key=f"btn_{t['id']}"):
                        with st.spinner("กำลังคุยกับ AI..."):
                            st.session_state[f"opts_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'], t['Persona'])
                    
                    if f"opts_{t['id']}" in st.session_state:
                        for i, msg in enumerate(st.session_state[f"opts_{t['id']}"]):
                            if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"sel_{t['id']}_{i}", use_container_width=True):
                                t['Draft'] = msg
                                st.rerun()

                    t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t['Draft'], key=f"dr_{t['id']}", height=150)
                    
                    if st.button("ส่งให้ Boss ตรวจ", key=f"sub_{t['id']}"):
                        t['Status'] = "Reviewing"
                        save_to_sheets(st.session_state.db)
                        st.rerun()
            else:
                st.success(f"✅ งาน '{t['Topic']}' ได้รับการอนุมัติแล้ว")

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
