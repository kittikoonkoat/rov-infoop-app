import streamlit as st
import pandas as pd
import requests

# --- 1. Gemini Dark Theme UI Styling ---
st.set_page_config(page_title="RoV Seeding - Gemini Edition", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* พื้นหลังสีเทาเข้มแบบ Gemini */
    .stApp {
        background-color: #131314;
        color: #E3E3E3;
    }
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    /* Sidebar แบบ Gemini */
    [data-testid="stSidebar"] {
        background-color: #1E1F20 !important;
        border-right: 1px solid #333537;
    }

    /* Input Box ทรงมนแบบช่องแชท AI */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important;
        color: #E3E3E3 !important;
        border: 1px solid #444746 !important;
        border-radius: 18px !important;
    }

    /* ปุ่มกดสีน้ำเงินไล่เฉด (Gemini Style) */
    div.stButton > button {
        border-radius: 20px;
        background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.6rem 2rem;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        background: #1A73E8;
        box-shadow: 0 0 15px rgba(66, 133, 244, 0.4);
        transform: translateY(-1px);
    }

    /* กล่องขยายความ (Expander) */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
    }

    /* หัวข้อและตัวเลขสถิติ */
    h1, h2, h3 { color: #FFFFFF !important; letter-spacing: -0.5px; }
    [data-testid="stMetricValue"] { color: #4285F4 !important; font-weight: 700; }
    
    /* ปรับแต่งตาราง */
    .stDataFrame, .stTable {
        background-color: #1E1F20;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ระบบจัดการข้อมูลผู้ใช้งาน ---
if 'users' not in st.session_state:
    st.session_state.users = {
        "kittikoon.k@garena.com": {"name": "คุณกิตติคุณ", "role": "Admin", "pass": "garena123"},
        "rov.pichsinee@garena.com": {"name": "น้องปลาย", "role": "PIC", "pass": "rov01"},
        "rov.jirapat@garena.com": {"name": "น้องกร", "role": "PIC", "pass": "rov02"},
        "rov.chaiwat@garena.com": {"name": "น้องเต้ย", "role": "PIC", "pass": "rov03"},
        "rov.thanakrit@garena.com": {"name": "น้องไทม์", "role": "PIC", "pass": "rov04"}
    }

if 'db' not in st.session_state:
    st.session_state.db = []

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. ฟังก์ชันเรียกใช้งาน API (อัปเดต Key แล้ว) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    # อัปเดต API Key ของคุณเรียบร้อยแล้ว
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f" 
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "garena_seeding_app"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        # ดึงข้อความจาก Node End (ตัวแปรชื่อ text)
        raw_text = result.get('data', {}).get('outputs', {}).get('text', "")
        # แยกข้อความออกเป็นลิสต์บรรทัด
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except Exception as e:
        return [f"การเชื่อมต่อผิดพลาด: {str(e)}"]

# --- 4. ระบบ Login ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Login")
    with st.container():
        st.write("เข้าสู่ระบบด้วยอีเมล @garena.com")
        email_input = st.text_input("Garena Email")
        pass_input = st.text_input("Password", type="password")
        if st.button("Login"):
            if email_input in st.session_state.users and st.session_state.users[email_input]["pass"] == pass_input:
                st.session_state.logged_in = True
                st.session_state.user_info = st.session_state.users[email_input]
                st.session_state.user_email = email_input
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- 5. เมนูและการนำทาง ---
user = st.session_state.user_info
st.sidebar.title(f"✨ สวัสดี, {user['name']}")
if st.sidebar.button("Log out"):
    st.session_state.logged_in = False
    st.rerun()

menu_options = ["PIC Workspace"]
if user['role'] == "Admin":
    menu_options = ["Admin Control", "PIC Workspace", "Daily Report", " User Management"]

choice = st.sidebar.selectbox("Navigate to", menu_options)

# --- 6. หน้าการทำงานแต่ละเมนู ---

# ---- หน้าจัดการ User (เฉพาะ Admin) ----
if choice == " User Management":
    st.title("👥 User Management")
    with st.expander("➕ เพิ่มสมาชิกใหม่"):
        with st.form("new_user_form"):
            u_email = st.text_input("Email (@garena.com)")
            u_name = st.text_input("ชื่อ-นามสกุล")
            u_pass = st.text_input("รหัสผ่านเริ่มต้น")
            u_role = st.selectbox("สิทธิ์", ["PIC", "Admin"])
            if st.form_submit_button("บันทึก"):
                st.session_state.users[u_email] = {"name": u_name, "role": u_role, "pass": u_pass}
                st.success(f"เพิ่ม {u_name} เรียบร้อย!")
                st.rerun()
    st.subheader("สมาชิกทั้งหมด")
    st.table(pd.DataFrame([{"Name": v['name'], "Email": k, "Role": v['role']} for k, v in st.session_state.users.items()]))

# ---- หน้าสั่งงาน (Admin Control) ----
elif choice == "Admin Control":
    st.title("👨‍💼 Admin Control")
    with st.form("task_form"):
        st.subheader("มอบหมายงานใหม่")
        col1, col2 = st.columns(2)
        t_topic = col1.text_input("หัวข้อ (Topic)")
        t_pic = col2.selectbox("มอบหมายให้", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
        t_guide = st.text_area("Message Guide")
        t_url = st.text_input("Target URL")
        if st.form_submit_button("Assign Task"):
            st.session_state.db.append({
                "id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic,
                "Guide": t_guide, "Target": t_url, "Status": "Waiting", "Draft": ""
            })
            st.success("ส่งงานสำเร็จ!")

# ---- หน้าคนทำงาน (PIC Workspace) ----
elif choice == "PIC Workspace":
    st.title("📱 PIC Workspace")
    my_tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    
    for t in my_tasks:
        with st.expander(f"📌 งาน: {t['Topic']} ({t['Status']})"):
            st.write(f"**Guide:** {t['Guide']}")
            if st.button("✨ ให้ AI ช่วยร่างข้อความ", key=f"ai_{t['id']}"):
                with st.spinner('Gemini Agent กำลังร่างข้อความ...'):
                    results = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                    st.session_state[f"res_{t['id']}"] = results
            
            if f"res_{t['id']}" in st.session_state:
                for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                    st.info(msg)
                    if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
            
            t['Draft'] = st.text_area("แก้ไข/สรุปข้อความสุดท้าย", value=t['Draft'], key=f"ed_{t['id']}")
            if st.button("ส่งให้ Admin ตรวจ", key=f"sub_{t['id']}"):
                t['Status'] = "Pending Approval"
                st.rerun()

# ---- หน้าสรุปงาน (Daily Report) ----
elif choice == "Daily Report":
    st.title("📊 Daily Summary")
    if st.session_state.db:
        st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
    else:
        st.write("ยังไม่มีข้อมูลงาน")
