import streamlit as st
import pandas as pd
import requests

# --- 1. iOS/macOS UI Styling ---
st.set_page_config(page_title="RoV Seeding Command Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #f5f5f7; border-right: 1px solid #d2d2d7; }
    div.stButton > button { border-radius: 12px; background-color: #007aff; color: white; font-weight: 600; }
    div[data-testid="stExpander"] { border-radius: 16px; border: 1px solid #d2d2d7; background-color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ระบบจัดการ User แบบ Dynamic ---
# ใช้ session_state เพื่อให้ Admin เพิ่ม/ลด User ได้จริง
if 'users' not in st.session_state:
    st.session_state.users = {
        "kittikoon.k@garena.com": {"name": "คุณกิตติคุณ", "role": "Admin", "pass": "garena123"},
        "rov.pichsinee@garena.com": {"name": "น้องปลาย", "role": "PIC", "pass": "rov01"},
        "rov.jirapat@garena.com": {"name": "น้องกร", "role": "PIC", "pass": "rov02"},
        "rov.chaiwat@garena.com": {"name": "น้องเต้ย", "role": "PIC", "pass": "rov03"},
        "rov.thanakrit@garena.com": {"name": "น้องไทม์", "role": "PIC", "pass": "rov04"}
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

# --- 3. หน้า Login ---
if not st.session_state.logged_in:
    st.title(" RoV Seeding Login")
    with st.form("login_form"):
        email = st.text_input("Garena Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if email in st.session_state.users and st.session_state.users[email]["pass"] == password:
                st.session_state.logged_in = True
                st.session_state.user_info = st.session_state.users[email]
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- 4. Sidebar & Menu Role-Based ---
user = st.session_state.user_info
st.sidebar.title(f"สวัสดี, {user['name']}")

if st.sidebar.button("Log out"):
    st.session_state.logged_in = False
    st.rerun()

# กรองเมนู: เฉพาะ Admin (คุณกิตติคุณ) ถึงจะเห็น "User Management"
menu_options = ["PIC Workspace"]
if user['role'] == "Admin":
    menu_options = ["Admin Control Center", "PIC Workspace", "Daily Report", " User Management"]

menu = st.sidebar.selectbox(" Menu", menu_options)

# --- 5. การทำงานแต่ละหน้า ---

# ---- หน้าจัดการ User (เฉพาะ Admin เท่านั้นที่เห็น) ----
if menu == " User Management":
    st.title(" User Management")
    st.write("จัดการสิทธิ์และรายชื่อทีมงาน @garena.com")

    # ส่วนเพิ่ม User ใหม่
    with st.expander("➕ เพิ่มสมาชิกทีมใหม่"):
        with st.form("add_user_form"):
            new_email = st.text_input("Email (@garena.com)")
            new_name = st.text_input("ชื่อ-นามสกุล")
            new_pass = st.text_input("Password")
            new_role = st.selectbox("สิทธิ์การใช้งาน", ["PIC", "Admin"])
            if st.form_submit_button("บันทึกพนักงานใหม่"):
                if "@garena.com" in new_email:
                    st.session_state.users[new_email] = {"name": new_name, "role": new_role, "pass": new_pass}
                    st.success(f"เพิ่ม {new_name} เข้าสู่ระบบแล้ว")
                    st.rerun()
                else:
                    st.error("ต้องเป็นอีเมล @garena.com เท่านั้น")

    # ตารางรายชื่อ User ปัจจุบัน
    st.subheader("👥 รายชื่อสมาชิกในทีม")
    user_list = []
    for email, info in st.session_state.users.items():
        user_list.append({"Email": email, "Name": info['name'], "Role": info['role']})
    
    st.table(pd.DataFrame(user_list))

    # ส่วนลบ User
    with st.expander("❌ ลบสมาชิกทีม"):
        delete_email = st.selectbox("เลือกอีเมลที่จะลบ", [e for e in st.session_state.users.keys() if e != st.session_state.user_email])
        if st.button("ยืนยันการลบพนักงาน"):
            del st.session_state.users[delete_email]
            st.warning(f"ลบ {delete_email} เรียบร้อยแล้ว")
            st.rerun()

# (หน้าที่เหลือ Admin Control, PIC Workspace คงไว้ตามเดิมจาก Code ก่อนหน้า)
elif menu == "Admin Control Center":
    st.title("👨‍💻 Admin Control Center")
    # ... (ส่วนการ Assign งานเหมือนเดิม)
    with st.form("add_task"):
        st.subheader("Assign New Task")
        t_name = st.text_input("Topic")
        t_pic = st.selectbox("Assign to PIC", [v['name'] for k, v in st.session_state.users.items() if v['role'] == "PIC"])
        t_guide = st.text_area("Message Guide")
        t_target = st.text_input("Target Group URL")
        if st.form_submit_button("Add Task"):
            if 'db' not in st.session_state: st.session_state.db = []
            st.session_state.db.append({
                "id": len(st.session_state.db)+1, "Topic": t_name, "PIC": t_pic, 
                "Guide": t_guide, "Target": t_target, "Status": "Waiting", "Draft": ""
            })
            st.success(f"ส่งงานให้ {t_pic} เรียบร้อย!")

elif menu == "PIC Workspace":
    st.title("📱 PIC Workspace")
    # ... (ส่วน PIC Workspace เหมือนเดิม)
    st.info("หน้านี้สำหรับร่างข้อความและส่งตรวจ")

elif menu == "Daily Report":
    st.title("📊 Daily Summary")
    if 'db' in st.session_state and st.session_state.db:
        st.table(pd.DataFrame(st.session_state.db))
    else:
        st.write("ยังไม่มีข้อมูลงานในระบบ")
