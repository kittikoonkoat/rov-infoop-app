import streamlit as st
import pandas as pd
import requests

# --- 1. UI Styling: Gemini Luxury Dark Mode ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    .stApp {
        background-color: #131314;
        color: #E3E3E3;
    }
    
    html, body, [class*="css"] { 
        font-family: 'Inter', -apple-system, sans-serif; 
    }

    /* Luxury Space Theme */
    [data-testid="stSidebar"] {
        background-color: #1E1F20 !important;
        border-right: 1px solid #333537;
    }

    /* Clean Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important;
        color: #FFFFFF !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    /* Gemini Gradient Buttons */
    div.stButton > button {
        border-radius: 24px;
        background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 2.5rem;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        box-shadow: 0 0 20px rgba(66, 133, 244, 0.4);
        transform: translateY(-2px);
    }

    /* Glass Cards */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }

    h1, h2, h3 { color: #FFFFFF !important; }
    
    /* High Visibility AI Box */
    .stInfo {
        background-color: #041E3C !important;
        color: #D3E3FD !important;
        border: 1px solid #0842A0 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Database & Auth ---
if 'users' not in st.session_state:
    st.session_state.users = {
        "kittikoon.k@garena.com": {"name": "คุณกิตติคุณ", "role": "Admin", "pass": "garena123"},
        "rov.pichsinee@garena.com": {"name": "น้องปลาย", "role": "PIC", "pass": "rov01"},
        "rov.jirapat@garena.com": {"name": "น้องกร", "role": "PIC", "pass": "rov02"},
        "rov.chaiwat@garena.com": {"name": "น้องเต้ย", "role": "PIC", "pass": "rov03"},
        "rov.thanakrit@garena.com": {"name": "น้องไทม์", "role": "PIC", "pass": "rov04"}
    }
if 'db' not in st.session_state: st.session_state.db = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. API Call (Optimized for text node) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "gemini_fixed_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        result = response.json()
        outputs = result.get('data', {}).get('outputs', {})
        # ดึงจาก key 'text' ตามภาพ image_1b96d8.png
        raw_text = outputs.get('text') or next(iter(outputs.values()), "")
        
        if not raw_text:
            return []
        
        # แยกข้อความ 10 ข้อ
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

# --- 4. Login System (Clean Version) ---
def show_login():
    st.markdown("<br><h1 style='text-align: center;'>✨ RoV Seeding Portal</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.form("login_portal"):
            u_email = st.text_input("Garena Email", placeholder="example@garena.com")
            u_pass = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Sign In"):
                if u_email in st.session_state.users and st.session_state.users[u_email]["pass"] == u_pass:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[u_email]
                    st.rerun()
                else:
                    st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

if not st.session_state.logged_in:
    show_login()
else:
    # --- 5. Main Application ---
    user = st.session_state.user_info
    st.sidebar.markdown(f"### 💎 User: {user['name']}")
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    menu = ["PIC Workspace"]
    if user['role'] == "Admin":
        menu = ["Admin Control", "PIC Workspace", "Daily Report", "Management"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Admin Control":
        st.title("👨‍💻 Admin Control")
        with st.expander("➕ Assign New Task", expanded=True):
            with st.form("task_f"):
                t_topic = st.text_input("หัวข้อ (Topic)")
                t_pic = st.selectbox("ผู้รับผิดชอบ", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
                t_guide = st.text_area("Guideline")
                if st.form_submit_button("Deploy Task"):
                    st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                    st.success("มอบหมายงานสำเร็จ!")

    elif choice == "PIC Workspace":
        st.title("📱 My Workspace")
        tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
        
        if not tasks: st.info("ยังไม่มีงานที่ได้รับมอบหมาย")
        
        for t in tasks:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('Gemini is generating...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                        if res:
                            st.session_state[f"res_{t['id']}"] = res
                        else:
                            st.error("AI ไม่ส่งข้อมูลกลับมา (ตรวจสอบการ Publish ใน Agent)")

                res_key = f"res_{t['id']}"
                if res_key in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[res_key]):
                        st.info(msg)
                        if st.button(f"เลือกข้อความแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                t['Draft'] = st.text_area("ข้อความสุดท้ายที่จะใช้", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                
                if st.button("ยืนยันส่งงาน (Submit)", key=f"sub_{t['id']}"):
                    t['Status'] = "Pending"
                    st.success("ส่งงานเรียบร้อย!")
                    st.rerun()

    elif choice == "Daily Report":
        st.title("📊 Daily Summary")
        if st.session_state.db: st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
        else: st.write("ไม่มีข้อมูลงาน")

    elif choice == "Management":
        st.title("👥 Team Management")
        st.table(pd.DataFrame([{"Name": v['name'], "Role": v['role']} for v in st.session_state.users.values()]))
