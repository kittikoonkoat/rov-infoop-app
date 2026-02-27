import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import re

# ==========================================
# 1. GOOGLE SHEETS CONNECTION SETUP (แก้ไขเพื่อใช้บน Cloud)
# ==========================================

def init_connection():
    """เชื่อมต่อกับ Google Sheets ผ่าน Streamlit Secrets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # ดึงข้อมูลจาก Secrets แทนการอ่านไฟล์ .json
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

def sync_data():
    """ดึงข้อมูลล่าสุดจาก Sheets มาไว้ในแอป"""
    sh = init_connection()
    if sh:
        st.session_state.db = sh.worksheet("tasks").get_all_records()
        st.session_state.users_db = sh.worksheet("users").get_all_records()
        st.session_state.channels = sh.worksheet("channels").get_all_records()
        st.sidebar.success("🔄 ข้อมูลซิงค์ล่าสุดแล้ว")

def save_data(worksheet_name, data_list):
    """บันทึกข้อมูลจากแอปกลับไปที่ Sheets"""
    sh = init_connection()
    if sh:
        ws = sh.worksheet(worksheet_name)
        ws.clear()
        if data_list:
            df = pd.DataFrame(data_list)
            ws.update([df.columns.values.tolist()] + df.values.tolist())

# ==========================================
# 2. AI AGENT CONNECTOR (INSEA AI)
# ==========================================

def call_ai_agent(topic, guide):
    """เรียกใช้ AI ช่วยร่างข้อความ"""
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": "กะเทย เล่น rov มานาน พูดจาจิกกัดแต่น่ารัก"
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        res = requests.post(api_url, json=payload, headers=headers, timeout=60).json()
        
        raw = ""
        if 'data' in res and 'outputs' in res['data']:
            raw = res['data']['outputs'].get('text', "")
        elif 'text' in res:
            raw = res.get('text', "")

        lines = [l.strip() for l in str(raw).split('\n') if len(l.strip()) > 2]
        return lines if lines else ["AI ยังคิดไม่ออก ลองกดใหม่อีกครั้งนะคะ"]
        
    except Exception as e:
        return [f"เกิดข้อผิดพลาดในการเรียก AI: {str(e)}"]

# ==========================================
# 3. UI & INITIALIZATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ==========================================
# 4. LOGIN SYSTEM
# ==========================================

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    col1, _ = st.columns([1, 1.5])
    with col1:
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            user = next((x for x in st.session_state.users_db if str(x['email']) == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

# ==========================================
# 5. MAIN APPLICATION
# ==========================================
else:
    st.sidebar.title(f"👤 {st.session_state.current_user}")
    
    if st.session_state.user_role == "Boss":
        menu = st.sidebar.radio("เมนูหัวหน้า:", ["Dashboard", "จัดการกลุ่ม FB", "ตรวจงาน (Approval)", "มอบหมายงาน", "จัดการแอดมิน"])
        
        if menu == "Dashboard":
            st.title("📊 สรุปรายงานประจำวัน")
            if st.session_state.db:
                df = pd.DataFrame(st.session_state.db)
                st.dataframe(df)
                st.metric("ยอดโพสต์รวม", df['Post_Count'].sum())
            else: st.info("ยังไม่มีข้อมูลงาน")

        elif menu == "จัดการกลุ่ม FB":
            st.title("📂 Facebook Channel Management")
            with st.form("add_channel"):
                g_name = st.text_input("ชื่อกลุ่ม")
                g_url = st.text_input("ลิงก์กลุ่ม (URL)")
                if st.form_submit_button("บันทึกกลุ่ม"):
                    st.session_state.channels.append({"group_name": g_name, "group_url": g_url})
                    save_data("channels", st.session_state.channels)
                    st.success("บันทึกกลุ่มใหม่แล้ว!")
                    st.rerun()
            st.write("กลุ่มทั้งหมดในระบบ:")
            st.table(pd.DataFrame(st.session_state.channels))

        elif menu == "มอบหมายงาน":
            st.title("🎯 Assign New Task")
            with st.form("assign_form"):
                topic = st.text_input("หัวข้อ (Topic)")
                guide = st.text_area("แนวทาง (Guideline)")
                admins = [u['email'] for u in st.session_state.users_db if u['role'] == "Admin"]
                pic = st.selectbox("เลือกแอดมินผู้รับผิดชอบ", admins)
                if st.form_submit_button("Deploy Task"):
                    st.session_state.db.append({
                        "id": len(st.session_state.db)+1, "Topic": topic, "Guide": guide, "PIC": pic,
                        "FB_Group_Name": "", "FB_Group_URL": "", "Draft": "", "Status": "Pending", "Post_Count": 0, "Comment_Count": 0
                    })
                    save_data("tasks", st.session_state.db)
                    st.success(f"ส่งงานให้ {pic} เรียบร้อย!")

        elif menu == "ตรวจงาน (Approval)":
            st.title("👀 Approve Seeding Content")
            review_list = [t for t in st.session_state.db if t['Status'] == "Reviewing"]
            if not review_list: st.info("ไม่มีงานรอตรวจ")
            for t in review_list:
                with st.expander(f"📌 {t['Topic']} (โดย {t['PIC']})", expanded=True):
                    st.write(f"จะโพสต์ที่กลุ่ม: **{t['FB_Group_Name']}**")
                    t['Draft'] = st.text_area("แก้ไขข้อความ:", value=t['Draft'], key=f"boss_{t['id']}")
                    if st.button("✅ Approve", key=f"app_{t['id']}"):
                        t['Status'] = "Approved"
                        save_data("tasks", st.session_state.db)
                        st.rerun()

        elif menu == "จัดการแอดมิน":
            st.title("👥 Admin Account Management")
            with st.form("add_admin"):
                new_e = st.text_input("Email แอดมิน")
                new_p = st.text_input("Password")
                if st.form_submit_button("สร้างบัญชี"):
                    st.session_state.users_db.append({"email": new_e, "password": new_p, "role": "Admin", "name": new_e.split('@')[0]})
                    save_data("users", st.session_state.users_db)
                    st.rerun()
            st.table(pd.DataFrame(st.session_state.users_db))

    else:
        menu = st.sidebar.radio("เมนูแอดมิน:", ["งานที่ได้รับมอบหมาย", "ส่งยอดประจำวัน"])
        
        if menu == "งานที่ได้รับมอบหมาย":
            st.title("📥 My Assigned Tasks")
            my_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]
            for t in my_jobs:
                with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                    if t['Status'] == "Pending":
                        channel_names = [c['group_name'] for c in st.session_state.channels]
                        selected_g = st.selectbox("เลือกกลุ่ม FB:", channel_names, key=f"g_{t['id']}")
                        g_info = next((c for c in st.session_state.channels if c['group_name'] == selected_g), None)
                        
                        t['FB_Group_Name'] = selected_g
                        t['FB_Group_URL'] = g_info['group_url'] if g_info else ""
                        
                        if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                            st.session_state[f"ai_res_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'])
                        
                        if f"ai_res_{t['id']}" in st.session_state:
                            for i, msg in enumerate(st.session_state[f"ai_res_{t['id']}"]):
                                if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                                    t['Draft'] = msg
                                    st.rerun()
                        
                        t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t['Draft'], key=f"ed_{t['id']}")
                        if st.button("ส่งให้หัวหน้าตรวจ", key=f"sub_{t['id']}"):
                            t['Status'] = "Reviewing"
                            save_data("tasks", st.session_state.db)
                            st.rerun()
                    
                    elif t['Status'] == "Approved":
                        st.success("✅ หัวหน้าอนุมัติแล้ว! ก๊อปปี้ไปโพสต์ได้เลย")
                        st.code(t['Draft'])
                        st.markdown(f'<a href="{t["FB_Group_URL"]}" target="_blank"><button style="background-color: #4267B2; color: white; border: none; padding: 12px 24px; border-radius: 12px; cursor: pointer; width: 100%;">เปิดกลุ่ม {t["FB_Group_Name"]} เพื่อโพสต์ 🚀</button></a>', unsafe_allow_html=True)

        elif menu == "ส่งยอดประจำวัน":
            st.title("📊 ปิดยอดสรุปวัน")
            done_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user and t['Status'] == "Approved"]
            for t in done_jobs:
                with st.container(border=True):
                    st.write(f"**งาน:** {t['Topic']} | **กลุ่ม:** {t['FB_Group_Name']}")
                    c1, c2 = st.columns(2)
                    t['Post_Count'] = c1.number_input("จำนวนโพสต์", value=t['Post_Count'], key=f"pc_{t['id']}")
                    t['Comment_Count'] = c2.number_input("จำนวนคอมเมนต์", value=t['Comment_Count'], key=f"cc_{t['id']}")
            if st.button("บันทึกตัวเลขยอดรวม"):
                save_data("tasks", st.session_state.db)
                st.success("บันทึกยอดลงระบบแล้ว!")

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
