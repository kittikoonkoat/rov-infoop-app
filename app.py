import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. การเชื่อมต่อ DATABASE
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
        st.error(f"❌ เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            # ดึงข้อมูลทุกหน้ามาเก็บใน Session
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.session_state.channels = sh.worksheet("channels").get_all_records()
            st.sidebar.success("🔄 ซิงค์ข้อมูลครบถ้วน")
        except Exception as e:
            st.error(f"⚠️ ตรวจสอบหัวคอลัมน์ใน Sheets: {e}")

def save_to_sheets(data_list):
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet("tasks")
            ws.clear()
            df = pd.DataFrame(data_list)
            ws.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            st.error(f"❌ บันทึกข้อมูลไม่ได้: {e}")

# ==========================================
# 3. MAIN APP LOGIC (Fix Login & Member Display)
# ==========================================
st.set_page_config(page_title="RoV Seeding Pro", layout="wide")

# บังคับซิงค์ข้อมูลถ้ายังไม่มี
if 'users_db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- ส่วนควบคุมการแสดงผลหน้าจอ ---
if not st.session_state.logged_in:
    # แสดงหน้า LOGIN เสมอหากยังไม่ได้ล็อกอิน
    st.title("💎 RoV Seeding Portal")
    with st.container():
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            user = next((x for x in st.session_state.get('users_db', []) if str(x['email']) == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
            else:
                st.error("❌ ข้อมูลไม่ถูกต้อง")
else:
    # หน้าจอหลักหลัง LOGIN
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    st.sidebar.write(st.session_state.current_user)
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    # แยกการแสดงผลตามสิทธิ์
    if st.session_state.user_role == "Boss":
        st.title("👨‍💼 Boss Assignment Panel")
        # (โค้ดส่วน Boss สำหรับสั่งงานและ Approve)
        
    elif st.session_state.user_role == "Admin":
        st.title("👩‍💻 My Assigned Tasks")
        # ดึงรายชื่อกลุ่มจากหน้า channels มาใช้
        channels = st.session_state.get('channels', [])
        fb_group_options = [c['group_name'] for c in channels] if channels else ["No Groups Found"]
        
        # แสดงรายการงาน (Tasks)
        for t in st.session_state.db:
            if t['PIC'] == st.session_state.current_user and t['Status'] != "Approved":
                with st.expander(f"📌 {t['Topic']} | {t['Status']}", expanded=True):
                    # แสดง dropdown เลือกกลุ่มที่ดึงมาจาก database
                    t['FB_Group'] = st.selectbox("เลือกกลุ่ม FB:", fb_group_options, 
                                                 index=fb_group_options.index(t['FB_Group']) if t.get('FB_Group') in fb_group_options else 0,
                                                 key=f"fb_{t['id']}")
                    # (โค้ดส่วน Admin สำหรับใส่ Guide/Persona และเรียก AI)
