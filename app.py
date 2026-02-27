import streamlit as st
import pandas as pd
import requests
import re

# --- 1. การตั้งค่าหน้าตาเว็บ (UI) ---
st.set_page_config(page_title="RoV Seeding Management System", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; }
    div.stButton > button { border-radius: 24px; font-weight: 500; }
    div.stButton > button:disabled { background: #333537 !important; color: #757575 !important; }
    .stTextInput input, .stTextArea textarea { background-color: #1E1F20 !important; color: #FFFFFF !important; border-radius: 12px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเตรียมฐานข้อมูลจำลอง (Initialization) ---
if 'db' not in st.session_state:
    st.session_state.db = []  # เก็บข้อมูลงานทั้งหมด

if 'users_db' not in st.session_state:
    # เริ่มต้นด้วยบัญชีคุณกิตติคุณ (Boss)
    st.session_state.users_db = [
        {"email": "kittikoon.k@garena.com", "password": "boss123", "role": "Boss", "name": "คุณกิตติคุณ"}
    ]

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None 
    st.session_state.current_user = ""

# --- 3. ฟังก์ชันเชื่อมต่อ Insea AI Agent ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "Topic": str(topic), "Guide": str(guide), "Persona": "กะเทย เล่น rov มานาน",
        "response_mode": "blocking", "user": "gemini_final"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        raw_output = res_data.get('data', {}).get('outputs', {}).get('text', "")
        if not raw_output: raw_output = res_data.get('text', "")
        lines = [l.strip() for l in str(raw_output).split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', line) for line in lines]
    except:
        return []

# --- 4. หน้าจอ Login ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Portal")
    col1, _ = st.columns([1, 1.5])
    with col1:
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            user = next((x for x in st.session_state.users_db if x['email'] == u_email and x['password'] == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
else:
    # --- 5. แถบเมนู (Sidebar) ---
    st.sidebar.title(f"👤 {st.session_state.current_user}")
    st.sidebar.info(f"Role: {st.session_state.user_role}")
    
    if st.session_state.user_role == "Boss":
        menu = st.sidebar.radio("เมนูหัวหน้า:", ["Dashboard (ภาพรวม)", "ตรวจงาน (Approval)", "มอบหมายงานใหม่", "จัดการ Admin Account"])
    else:
        menu = st.sidebar.radio("เมนูแอดมิน:", ["งานที่ได้รับมอบหมาย", "ส่งยอดประจำวัน"])

    # --- 6. [BOSS] หน้าจัดการ Admin Account ---
    if menu == "จัดการ Admin Account":
        st.title("👥 จัดการรายชื่อ Admin")
        with st.expander("➕ เพิ่ม Admin ใหม่", expanded=True):
            new_e = st.text_input("อีเมลแอดมิน")
            new_p = st.text_input("กำหนดรหัสผ่าน")
            if st.button("บันทึกบัญชี"):
                if new_e and new_p and "@" in new_e:
                    st.session_state.users_db.append({"email": new_e, "password": new_p, "role": "Admin", "name": new_e.split('@')[0]})
                    st.success(f"เพิ่ม {new_e} เรียบร้อย!")
                    st.rerun()
        
        st.subheader("📋 บัญชีแอดมินทั้งหมด")
        admin_list = [u for u in st.session_state.users_db if u['role'] == "Admin"]
        if admin_list:
            st.table(pd.DataFrame(admin_list)[['email', 'password']])
            del_target = st.selectbox("เลือกอีเมลที่จะลบ:", [u['email'] for u in admin_list])
            if st.button("ลบบัญชีที่เลือก"):
                st.session_state.users_db = [u for u in st.session_state.users_db if u['email'] != del_target]
                st.success(f"ลบ {del_target} สำเร็จ")
                st.rerun()
        else:
            st.info("ยังไม่มีแอดมินในระบบ")

    # --- 7. [BOSS] หน้ามอบหมายงานใหม่ ---
    elif menu == "มอบหมายงานใหม่":
        st.title("🎯 Assign New Task")
        with st.form("new_task"):
            nt = st.text_input("หัวข้อ (Topic)")
            ng = st.text_area("แนวทาง (Guideline)")
            admins = [u['email'] for u in st.session_state.users_db if u['role'] == "Admin"]
            np = st.selectbox("มอบหมายให้แอดมินคนไหน:", admins if admins else ["ยังไม่มีแอดมินในระบบ"])
            if st.form_submit_button("Deploy Task") and admins:
                st.session_state.db.append({
                    "id": len(st.session_state.db)+1, "Topic": nt, "Guide": ng, "PIC": np,
                    "FB_Group": "", "Draft": "", "Status": "Pending", "Post_Count": 0, "Comment_Count": 0
                })
                st.success("จ่ายงานสำเร็จ!")

    # --- 8. [BOSS] หน้าตรวจงาน Approval ---
    elif menu == "ตรวจงาน (Approval)":
        st.title("👀 Approve Seeding Content")
        review_tasks = [t for t in st.session_state.db if t['Status'] == "Reviewing"]
        if not review_tasks: st.info("ไม่มีงานรอตรวจในขณะนี้")
        for t in review_tasks:
            with st.expander(f"📌 {t['Topic']} (โดย {t['PIC']})", expanded=True):
                st.write(f"**กลุ่มที่จะโพสต์:** {t['FB_Group']}")
                # หัวหน้าแก้ไขข้อความแอดมินได้
                t['Draft'] = st.text_area("ร่างข้อความ (แก้ไขได้):", value=t['Draft'], key=f"boss_ed_{t['id']}")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"app_{t['id']}"):
                    t['Status'] = "Approved"
                    st.rerun()
                if c2.button("❌ Reject (ตีกลับไปแก้)", key=f"rej_{t['id']}"):
                    t['Status'] = "Pending"
                    st.rerun()

    # --- 9. [ADMIN] งานที่ได้รับมอบหมาย ---
    elif menu == "งานที่ได้รับมอบหมาย":
        st.title("📥 My Assigned Tasks")
        my_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]
        if not my_jobs: st.info("ยังไม่มีงานที่คุณได้รับมอบหมาย")
        for t in my_jobs:
            with st.expander(f"📌 {t['Topic']} - สถานะ: {t['Status']}", expanded=True):
                if t['Status'] == "Pending":
                    st.write(f"**แนวทาง:** {t['Guide']}")
                    if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                        res = call_seeding_agent(t['Topic'], t['Guide'])
                        if res: st.session_state[f"res_list_{t['id']}"] = res
                    
                    if f"res_list_{t['id']}" in st.session_state:
                        for i, msg in enumerate(st.session_state[f"res_list_{t['id']}"]):
                            if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                                st.session_state[f"ed_{t['id']}"] = msg
                                t['Draft'] = msg
                                st.rerun()
                    
                    t['FB_Group'] = st.text_input("ระบุชื่อ Facebook Group ที่จะไปโพสต์:", value=t['FB_Group'], key=f"grp_{t['id']}")
                    t['Draft'] = st.text_area("ข้อความที่จะส่งตรวจ:", key=f"ed_{t['id']}", value=t['Draft'])
                    if st.button("ส่งให้หัวหน้าตรวจ", key=f"sub_{t['id']}", disabled=not (t['Draft'] and t['FB_Group'])):
                        t['Status'] = "Reviewing"
                        st.rerun()
                elif t['Status'] == "Approved":
                    st.success("✅ อนุมัติแล้ว! ก๊อปปี้ไปโพสต์ได้เลย:")
                    st.code(t['Draft'])

    # --- 10. [ADMIN] ส่งยอดประจำวัน ---
    elif menu == "ส่งยอดประจำวัน":
        st.title("📊 Report Daily Counts")
        done_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user and t['Status'] == "Approved"]
        for t in done_jobs:
            with st.container(border=True):
                st.write(f"**งาน:** {t['Topic']} | **กลุ่ม:** {t['FB_Group']}")
                c1, c2 = st.columns(2)
                t['Post_Count'] = c1.number_input("จำนวนโพสต์", value=t['Post_Count'], key=f"pc_{t['id']}")
                t['Comment_Count'] = c2.number_input("จำนวนคอมเมนต์", value=t['Comment_Count'], key=f"cc_{t['id']}")

    # --- 11. Dashboard (Dashboard สำหรับ Boss) ---
    elif menu == "Dashboard (ภาพรวม)":
        st.title("📋 สรุปผลการทำงาน")
        if st.session_state.db:
            df = pd.DataFrame(st.session_state.db)
            st.dataframe(df[['PIC', 'Topic', 'FB_Group', 'Status', 'Post_Count', 'Comment_Count']])
            col1, col2 = st.columns(2)
            col1.metric("ยอดโพสต์รวม", df['Post_Count'].sum())
            col2.metric("ยอดคอมเมนต์รวม", df['Comment_Count'].sum())
        else: st.info("ยังไม่มีข้อมูลงาน")

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
