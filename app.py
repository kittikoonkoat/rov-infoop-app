import streamlit as st
import pandas as pd
import requests

# --- 1. Apple Store Luxury UI Styling ---
st.set_page_config(page_title="RoV Seeding Command Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global Apple White Theme */
    .stApp { background-color: #FFFFFF; color: #1d1d1f; }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }

    /* Sidebar - Apple Gray Navigation */
    [data-testid="stSidebar"] {
        background-color: #f5f5f7 !important;
        border-right: 1px solid #d2d2d7;
    }

    /* Input Fields - Clean & Sharp Borders */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #1d1d1f !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-size: 16px !important;
    }
    
    /* High-end Pill Buttons (Apple Blue) */
    div.stButton > button {
        border-radius: 20px;
        background-color: #0071e3;
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 2rem;
        transition: 0.2s;
    }
    div.stButton > button:hover { background-color: #0077ed; transform: scale(1.02); }

    /* Luxury Cards (Expander) */
    div[data-testid="stExpander"] {
        border-radius: 18px !important;
        border: 1px solid #d2d2d7 !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
    }

    /* Headings & Text */
    h1, h2, h3 { color: #1d1d1f !important; font-weight: 600 !important; }
    .stMarkdown p { color: #1d1d1f; font-weight: 400; }
    
    /* Blue Accents for Seeding Content */
    .stInfo {
        background-color: #f5f5f7 !important;
        color: #0071e3 !important;
        border: 1px solid #0071e3 !important;
        border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Persistence (Session State) ---
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

# --- 3. AI Agent Connector (Fixed for text variable) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "garena_apple_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        outputs = result.get('data', {}).get('outputs', {})
        # ดึงจาก key 'text' ตามภาพ image_1b96d8.png
        raw_text = outputs.get('text') or next(iter(outputs.values()), "")
        if not raw_text: return ["⚠️ ไม่มีข้อความส่งกลับมา"]
        # แยกข้อความ 10 บรรทัด
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except Exception as e:
        return [f"❌ Error: {str(e)}"]

# --- 4. Sign-in Experience ---
if not st.session_state.logged_in:
    st.markdown("<br><h1 style='text-align: center;'> Sign in to RoV Seeding</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        with st.form("apple_login"):
            email = st.text_input("Garena Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if email in st.session_state.users and st.session_state.users[email]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[email]
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")
    st.stop()

# --- 5. Navigation ---
user = st.session_state.user_info
st.sidebar.markdown(f"###  สวัสดี, {user['name']}")
if st.sidebar.button("Sign Out"):
    st.session_state.logged_in = False
    st.rerun()

menu = st.sidebar.selectbox("Go to", ["Admin Control", "PIC Workspace", "Daily Report", " User Management"] if user['role'] == "Admin" else ["PIC Workspace"])

# --- 6. Content Pages ---

if menu == "Admin Control":
    st.title("👨‍💻 Admin Control Center")
    with st.expander("Assign New Seeding Task"):
        with st.form("task_f"):
            t_topic = st.text_input("Topic")
            t_pic = st.selectbox("Assign to", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
            t_guide = st.text_area("Guideline")
            if st.form_submit_button("Deploy"):
                st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                st.success("Task Deployed Successfully")

elif menu == "PIC Workspace":
    st.title("📱 My Workspace")
    tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    if not tasks: st.info("No active tasks.")
    for t in tasks:
        with st.expander(f"📌 {t['Topic']} — {t['Status']}"):
            st.write(f"**Guide:** {t['Guide']}")
            if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                with st.spinner('Apple Intelligence is drafting...'):
                    st.session_state[f"res_{t['id']}"] = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
            
            # แก้ไข Syntax บรรทัด 180 (Fixed)
            if f"res_{t['id']}" in st.session_state:
                st.markdown("---")
                for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                    st.info(msg)
                    if st.button(f"Choose Version {i+1}", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
            
            t['Draft'] = st.text_area("Final Content", value=t['Draft'], key=f"ed_{t['id']}")
            if st.button("Submit for Review", key=f"sub_{t['id']}"):
                t['Status'] = "Pending Approval"
                st.rerun()

elif menu == "Daily Report":
    st.title("📊 Daily Summary")
    if st.session_state.db: st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
    else: st.write("System is empty.")

elif menu == " User Management":
    st.title("👥 Team Management")
    st.table(pd.DataFrame([{"Name": v['name'], "Email": k, "Role": v['role']} for k, v in st.session_state.users.items()]))
