import streamlit as st
import pandas as pd
import requests

# --- 1. Gemini Luxury Dark UI Styling ---
st.set_page_config(page_title="RoV Seeding - Gemini Luxury", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global Gemini Dark Theme */
    .stApp {
        background-color: #131314;
        color: #E3E3E3;
    }
    
    html, body, [class*="css"] { 
        font-family: 'Inter', -apple-system, sans-serif; 
    }

    /* Sidebar - Deep Dark Navigation */
    [data-testid="stSidebar"] {
        background-color: #1E1F20 !important;
        border-right: 1px solid #333537;
    }

    /* Clean & High-end Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important;
        color: #FFFFFF !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        transition: 0.3s;
    }
    
    .stTextInput input:focus {
        border-color: #8E918F !important;
    }

    /* Gemini Blue Buttons (Rounded & Minimal) */
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
        transform: translateY(-1px);
    }

    /* Luxury Glassmorphism Cards (Expanders) */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
        margin-bottom: 15px;
    }

    /* Headings & Metrics */
    h1, h2, h3 { 
        color: #FFFFFF !important; 
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    
    /* Info Box for AI Results */
    .stInfo {
        background-color: #041E3C !important;
        color: #D3E3FD !important;
        border: 1px solid #0842A0 !important;
        border-radius: 12px !important;
    }

    /* Table Style */
    .stDataFrame {
        border: 1px solid #444746;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Persistence ---
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

# --- 3. AI Agent Connector (Fixed for Node End: text) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "gemini_luxury_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        outputs = result.get('data', {}).get('outputs', {})
        # ดึงจาก key 'text' ตามภาพ image_1b96d8.png
        raw_text = outputs.get('text') or next(iter(outputs.values()), "")
        if not raw_text: return ["⚠️ AI ไม่ได้ส่งข้อความกลับมา ลองตรวจสอบ Node End ครับ"]
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except:
        return ["❌ การเชื่อมต่อ API ล้มเหลว"]

# --- 4. Login System ---
if not st.session_state.logged_in:
    st.markdown("<br><h1 style='text-align: center;'>✨ Sign in to RoV Seeding</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        with st.form("gemini_login"):
            email = st.text_input("Garena Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                if email in st.session_state.users and st.session_state.users[email]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[email]
                    st.rerun()
                else: st.error("Email หรือ Password ไม่ถูกต้อง")
    st.stop()

# --- 5. Navigation ---
user = st.session_state.user_info
st.sidebar.markdown(f"### ✨ {user['name']}")
if st.sidebar.button("Sign Out"):
    st.session_state.logged_in = False
    st.rerun()

menu_list = ["PIC Workspace"]
if user['role'] == "Admin":
    menu_list = ["Admin Control", "PIC Workspace", "Daily Report", "User Management"]
choice = st.sidebar.selectbox("เมนูการใช้งาน", menu_list)

# --- 6. Pages ---

if choice == "Admin Control":
    st.title("👨‍💻 Admin Control Center")
    with st.expander("➕ มอบหมายงานใหม่ (New Task)"):
        with st.form("task_form"):
            t_topic = st.text_input("หัวข้อ (Topic)")
            t_pic = st.selectbox("ผู้รับผิดชอบ", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
            t_guide = st.text_area("แนวทาง (Guideline)")
            if st.form_submit_button("Deploy Task"):
                st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                st.success("ส่งงานเรียบร้อยแล้ว!")

elif choice == "PIC Workspace":
    st.title("📱 PIC Workspace")
    tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    if not tasks: st.info("ยังไม่มีงานในรายการ")
    for t in tasks:
        with st.expander(f"📌 {t['Topic']} — {t['Status']}"):
            st.write(f"**แนวทาง:** {t['Guide']}")
            if st.button("✨ ให้ AI ช่วยร่างข้อความ", key=f"ai_{t['id']}"):
                with st.spinner('Gemini กำลังร่างข้อความให้คุณ...'):
                    st.session_state[f"res_{t['id']}"] = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
            
            res_key = f"res_{t['id']}"
            if res_key in st.session_state:
                st.markdown("---")
                for i, msg in enumerate(st.session_state[res_key]):
                    st.info(msg)
                    if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
            
            t['Draft'] = st.text_area("ข้อความสุดท้าย
