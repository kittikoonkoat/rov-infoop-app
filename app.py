import streamlit as st
import pandas as pd
import requests

# --- 1. Apple Store Luxury UI Styling ---
st.set_page_config(page_title="RoV Seeding Command Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global Apple Style: White Background & Dark Text */
    .stApp { background-color: #FFFFFF; color: #1d1d1f; }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }

    /* Navigation Sidebar - Light Gray Apple Style */
    [data-testid="stSidebar"] {
        background-color: #f5f5f7 !important;
        border-right: 1px solid #d2d2d7;
    }

    /* Input Fields & Text Areas */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-basWeb="select"] {
        background-color: #ffffff !important;
        color: #1d1d1f !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-size: 16px !important;
    }
    
    /* Apple Blue Buttons (Rounded) */
    div.stButton > button {
        border-radius: 22px;
        background-color: #0071e3;
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 2.2rem;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #0077ed;
        transform: scale(1.02);
    }

    /* Luxury Container Cards (Expanders) */
    div[data-testid="stExpander"] {
        border-radius: 18px !important;
        border: 1px solid #e5e5e7 !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        margin-bottom: 20px;
    }

    /* Headings & Metrics */
    h1, h2, h3 { color: #1d1d1f !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #0071e3 !important; }

    /* Hide Streamlit Header/Footer for Premium Look */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
        # ดึงจาก key 'text' ตามรูปที่ให้มา
        raw_text = outputs.get('text') or next(iter(outputs.values()), "")
        if not raw_text: return ["⚠️ ไม่มีข้อความร่างส่งกลับมา"]
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except Exception as e:
        return [f"❌ Error: {str(e)}"]

# --- 4. Login Experience ---
if not st.session_state.logged_in:
    st.markdown("<br><h1 style='text-align: center;'> Sign in to RoV Seeding</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,2,1])
    with col:
        with st.form("apple_signin"):
            email = st.text_input("Garena Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if email in st.session_state.users and st.session_state.users[email]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[email]
                    st.rerun()
                else: st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- 5. Side Navigation ---
user = st.session_state.user_info
st.sidebar.markdown(f"###  สวัสดี, {user['name']}")
if st.sidebar.button("Sign Out"):
    st.session_state.logged_in = False
    st.rerun()

menu_list = ["PIC Workspace"]
if user['role'] == "Admin":
    menu_list = ["Admin Control", "PIC Workspace", "Daily Report", " User Management"]
choice = st.sidebar.selectbox("Go to", menu_list)

# --- 6. Content Pages ---

if choice == "Admin Control":
    st.title("👨‍💻 Admin Control Center")
    with st.expander("Assign New Seeding Task"):
        with st.form("task_f"):
            t_topic = st.text_input("Topic")
            t_pic = st.selectbox("Assign to", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
            t_guide = st.text_area("Guideline")
            if st.form_submit_button("Deploy Task"):
                st.session_state.db.append({
                    "id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic,
                    "Guide": t_guide, "Status": "Waiting", "Draft": ""
                })
                st.success("Task Deployed Successfully")

elif choice == "PIC Workspace":
    st.title("📱 My Workspace")
    tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    if not tasks: st.info("ไม่มีงานที่ค้างอยู่")
    for t in tasks:
        with st.expander(f"📌 {t['Topic']} — {t['Status']}"):
            st.write(f"**Guide:** {t['Guide']}")
            if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                with st.spinner('Apple Intelligence is drafting...'):
                    st.session_state[f"res_{t['id']}"] = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
            
            # แก้ไข Syntax Error บรรทัด 180 (Fixed)
            res_key = f"res_{t['id']}"
            if res_key in st.session_state:
                st.markdown("---")
                for i, msg in enumerate(st.session_state[res_key]):
                    st.info(msg)
                    if st.button(f"Choose Version {i+1}", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
            
            t['Draft'] = st.text_area("Final Content", value=t['Draft'], key=f"ed_{t['id']}")
            if st.button("Submit for Review", key=f"sub_{t['id']}"):
                t['Status'] = "Pending Approval"
                st.rerun()

elif choice == "Daily Report":
    st.title("📊 Daily Summary")
    if st.session_state.db: st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
    else: st.write("ยังไม่มีข้อมูลในระบบ")

elif choice == " User Management":
    st.title("👥 Team Management")
    st.table(pd.DataFrame([{"Name": v['name'], "Email": k, "Role": v['role']} for k, v in st.session_state.users.items()]))
