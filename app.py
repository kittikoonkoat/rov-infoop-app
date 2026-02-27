import streamlit as st
import pandas as pd
import requests

# --- 1. Apple Store Online UI Styling ---
st.set_page_config(page_title="RoV Seeding Command Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Apple Global Style */
    .stApp {
        background-color: #FFFFFF;
        color: #1d1d1f;
    }
    
    html, body, [class*="css"] { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
    }

    /* Navigation Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f5f5f7 !important;
        border-right: 1px solid #d2d2d7;
    }

    /* Input Fields Style (Apple Store Search Box Style) */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #1d1d1f !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        font-size: 16px !important;
    }
    
    .stTextInput input:focus {
        border-color: #0071e3 !important;
        box-shadow: 0 0 0 4px rgba(0,113,227,0.1) !important;
    }

    /* High-end Buttons (Apple Blue) */
    div.stButton > button {
        border-radius: 22px;
        background-color: #0071e3;
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 1.8rem;
        transition: all 0.2s ease-in-out;
    }
    
    div.stButton > button:hover {
        background-color: #0077ed;
        transform: scale(1.02);
    }

    /* Luxury Container / Cards */
    div[data-testid="stExpander"] {
        border-radius: 18px !important;
        border: 1px solid #d2d2d7 !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        margin-bottom: 20px;
    }

    /* Headers */
    h1, h2, h3 {
        color: #1d1d1f !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    /* Data Table Customization */
    .stDataFrame {
        border: 1px solid #d2d2d7;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Storage ---
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

# --- 3. API Function (Updated for Node End image_1b96d8.png) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f" 
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "apple_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        outputs = result.get('data', {}).get('outputs', {})
        
        # ดึงจาก key 'text' ตามรูป image_1b96d8.png
        raw_text = outputs.get('text') or next(iter(outputs.values()), "")
        
        if not raw_text:
            return ["ระบบขัดข้อง: ไม่พบข้อมูลจาก Agent"]
            
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except:
        return ["ไม่สามารถเชื่อมต่อ Agent ได้"]

# --- 4. Login System ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'> Sign in to RoV Seeding</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            email = st.text_input("Garena Email")
            password = st.text_input("Password", type="password")
            if st.button("Sign In"):
                if email in st.session_state.users and st.session_state.users[email]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[email]
                    st.rerun()
                else:
                    st.error("Apple ID หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- 5. Navigation ---
user = st.session_state.user_info
st.sidebar.markdown(f"###  สวัสดี, {user['name']}")
if st.sidebar.button("Sign Out"):
    st.session_state.logged_in = False
    st.rerun()

menu_options = ["PIC Workspace"]
if user['role'] == "Admin":
    menu_options = ["Admin Control Center", "PIC Workspace", "Daily Report", " User Management"]

choice = st.sidebar.selectbox("Go to", menu_options)

# --- 6. Pages ---

if choice == "Admin Control Center":
    st.title("👨‍💻 Admin Control Center")
    with st.expander("Assign New Task"):
        with st.form("task_form"):
            t_topic = st.text_input("Topic")
            t_pic = st.selectbox("Assign to", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
            t_guide = st.text_area("Guideline")
            if st.form_submit_button("Deploy"):
                st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                st.success("Task Deployed Successfully")

elif choice == "PIC Workspace":
    st.title("📱 My Workspace")
    tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    for t in tasks:
        with st.expander(f"📌 {t['Topic']} — {t['Status']}"):
            st.write(f"**Guide:** {t['Guide']}")
            if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                with st.spinner('Apple Intelligence is working...'):
                    results = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                    st.session_state[f"res_{t['id']}"] = results
            
            if f"res_{t['id']}" in st.
