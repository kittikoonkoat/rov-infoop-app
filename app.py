import streamlit as st
import pandas as pd
import requests

# --- 1. UI Styling: Gemini Dark Luxury ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    .stApp { background-color: #131314; color: #E3E3E3; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Sidebar Luxury Navigation */
    [data-testid="stSidebar"] {
        background-color: #1E1F20 !important;
        border-right: 1px solid #333537;
    }

    /* Modern Input & Text Area */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important;
        color: #FFFFFF !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    /* Gemini Signature Button */
    div.stButton > button {
        border-radius: 24px;
        background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 2.5rem;
        transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div.stButton > button:hover {
        box-shadow: 0 0 25px rgba(66, 133, 244, 0.4);
        transform: translateY(-2px);
    }

    /* AI Draft Box - High Contrast */
    .stInfo {
        background-color: #041E3C !important;
        color: #D3E3FD !important;
        border: 1px solid #0842A0 !important;
        border-radius: 14px !important;
        padding: 18px !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    /* Glassmorphism Expander */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
        margin-bottom: 20px;
    }
    
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 600 !important; letter-spacing: -0.01em; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Session Management ---
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

# --- 3. Optimized AI Connector (New API Key Applied) ---
def call_seeding_agent(topic, guide, persona):
    # อัปเดตข้อมูลใหม่ตามที่ได้รับ
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "gemini_luxury_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # ดึงจาก key 'text' ตามภาพ image_1aae73.png
        outputs = res_data.get('data', {}).get('outputs', {})
        raw_text = outputs.get('text', "")
        
        if not raw_text: return []
            
        # แยกข้อความ (Split by \n) กรองเอาเฉพาะบรรทัดที่ยาวพอจะเป็นประโยค
        messages = [line.strip() for line in str(raw_text).split('\n') if len(line.strip()) > 5]
        return messages
    except Exception as e:
        return []

# --- 4. Navigation & Logic ---
if not st.session_state.logged_in:
    # Clean Login Interface
    st.markdown("<br><h1 style='text-align: center;'>✨ Sign in to YA-MO-Project</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.form("login_ui"):
            u_email = st.text_input("Garena Email")
            u_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if u_email in st.session_state.users and st.session_state.users[u_email]["pass"] == u_pass:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[u_email]
                    st.rerun()
                else: st.error("ข้อมูลการเข้าสู่ระบบไม่ถูกต้อง")
else:
    # Dashboard Menu
    user = st.session_state.user_info
    st.sidebar.markdown(f"### 💎 {user['name']}")
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    menu_options = ["PIC Workspace", "Daily Report"]
    if user['role'] == "Admin": menu_options = ["Admin Control", "PIC Workspace", "Daily Report"]
    choice = st.sidebar.selectbox("Navigation", menu_options)

    if choice == "Admin Control":
        st.title("👨‍💻 Admin Control")
        with st.expander("➕ มอบหมายงานใหม่ (Assign Task)", expanded=True):
            with st.form("task_form"):
                t_topic = st.text_input("หัวข้อ (Topic)")
                t_pic = st.selectbox("Assign to", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
                t_guide = st.text_area("Guideline")
                if st.form_submit_button("Deploy"):
                    st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                    st.success("ส่งงานเข้าสู่ระบบเรียบร้อย")

    elif choice == "PIC Workspace":
        st.title("📱 My Workspace")
        tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
        
        if not tasks: st.info("ยังไม่มีงานในรายการ")
        
        for t in tasks:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**แนวทาง:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('Gemini กำลังร่างข้อความทั้ง 10 รูปแบบ...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                        if res: st.session_state[f"res_{t['id']}"] = res
                        else: st.error("AI ไม่ตอบกลับ (ตรวจสอบการ Publish ใน Insea Agent)")

                # Display AI Options
                res_key = f"res_{t['id']}"
                if res_key in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[res_key]):
                        st.info(msg)
                        if st.button(f"เลือกข้อความชุดที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                            st.success(f"เลือกเวอร์ชัน {i+1} สำเร็จ!")
                
                t['Draft'] = st.text_area("Final Draft (แก้ไขได้)", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                
                if st.button("ยืนยันการส่ง (Submit)", key=f"sub_{t['id']}"):
                    t['Status'] = "Pending Approval"
                    st.rerun()

    elif choice == "Daily Report":
        st.title("📊 Daily Summary")
        if st.session_state.db: st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
        else: st.write("ไม่มีข้อมูลงานในขณะนี้")
