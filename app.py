import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. iOS/macOS Light Mode UI Styling ---
st.set_page_config(page_title="RoV Seeding Command Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* Global Styles */
    .stApp { background-color: #FFFFFF; color: #1d1d1f; }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }

    /* Sidebar - macOS Style */
    [data-testid="stSidebar"] { background-color: #F2F2F7 !important; border-right: 1px solid #D2D2D7; }
    
    /* Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #1d1d1f !important;
        border: 1px solid #D2D2D7 !important;
        border-radius: 10px !important;
    }

    /* Apple Style Buttons */
    div.stButton > button {
        border-radius: 10px;
        background-color: #007AFF;
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #0056b3; color: white; transform: translateY(-1px); }

    /* Cards & Containers */
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #E5E5E7 !important;
        background-color: #FBFBFD !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] { color: #007AFF !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Data Storage (Session State) ---
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
    st.session_state.user_info = None

# --- 3. API Connector ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    # บรรทัดข้างล่างนี้ รบกวนคุณกิตติคุณนำ API Key มาใส่แทนนะครับ
    api_key = "jBF0ri1P76TwxBob6MlJ12chr4ch2pEL" 
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "garena_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        raw_text = result.get('data', {}).get('outputs', {}).get('text', "")
        return [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 5]
    except Exception as e:
        return [f"Error: {str(e)}"]

# --- 4. Authentication Flow ---
if not st.session_state.logged_in:
    st.title(" RoV Seeding Login")
    with st.container():
        st.write("Login with your @garena.com account")
        email_input = st.text_input("Email")
        pass_input = st.text_input("Password", type="password")
        if st.button("Login"):
            if email_input in st.session_state.users and st.session_state.users[email_input]["pass"] == pass_input:
                st.session_state.logged_in = True
                st.session_state.user_info = st.session_state.users[email_input]
                st.session_state.user_email = email_input
                st.rerun()
            else:
                st.error("Invalid email or password")
    st.stop()

# --- 5. Navigation ---
user = st.session_state.user_info
st.sidebar.title(f" {user['name']}")
st.sidebar.caption(f"Logged in as: {user['role']}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

menu_options = ["PIC Workspace"]
if user['role'] == "Admin":
    menu_options = ["Admin Control Center", "PIC Workspace", "Daily Report", " User Management"]

menu = st.sidebar.selectbox("Navigate to", menu_options)

# --- 6. Page Content ---

# ---- PAGE: USER MANAGEMENT ----
if menu == " User Management":
    st.title(" User Management")
    
    with st.expander("➕ Add New Team Member"):
        with st.form("new_user"):
            u_email = st.text_input("Garena Email")
            u_name = st.text_input("Full Name")
            u_pass = st.text_input("Initial Password")
            u_role = st.selectbox("Role", ["PIC", "Admin"])
            if st.form_submit_button("Save User"):
                if "@garena.com" in u_email:
                    st.session_state.users[u_email] = {"name": u_name, "role": u_role, "pass": u_pass}
                    st.success(f"Added {u_name} to the team!")
                    st.rerun()
                else:
                    st.error("Email must be @garena.com")

    st.subheader("Current Members")
    df_users = pd.DataFrame([{"Email": k, "Name": v['name'], "Role": v['role']} for k, v in st.session_state.users.items()])
    st.table(df_users)

# ---- PAGE: ADMIN CONTROL CENTER ----
elif menu == "Admin Control Center":
    st.title("👨‍💻 Admin Control Center")
    with st.form("new_task"):
        st.subheader("Assign New Seeding Task")
        col1, col2 = st.columns(2)
        t_topic = col1.text_input("Topic")
        t_pic = col2.selectbox("Assign to PIC", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
        t_guide = st.text_area("Message Guide / Angle")
        t_url = st.text_input("Target URL (Group/Page)")
        if st.form_submit_button("Deploy Task"):
            st.session_state.db.append({
                "id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic,
                "Guide": t_guide, "Target": t_url, "Status": "Waiting", "Draft": ""
            })
            st.success("Task assigned successfully!")

    st.divider()
    st.subheader("🕒 Review Pending Drafts")
    for t in st.session_state.db:
        if t['Status'] == "Pending":
            with st.expander(f"Review: {t['Topic']} by {t['PIC']}"):
                st.info(t['Draft'])
                if st.button("Approve & Finalize", key=f"app_{t['id']}"):
                    t['Status'] = "Approved"
                    st.rerun()

# ---- PAGE: PIC WORKSPACE ----
elif menu == "PIC Workspace":
    st.title("📱 PIC Workspace")
    # Admin sees all, PIC sees only their tasks
    my_tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    
    if not my_tasks:
        st.write("No tasks assigned yet. Chill out! ☕️")
    
    for t in my_tasks:
        with st.expander(f"📌 {t['Topic']} - Status: {t['Status']}"):
            st.write(f"**Guide:** {t['Guide']}")
            
            if st.button("✨ Ask AI Agent to Draft", key=f"ai_{t['id']}"):
                with st.spinner('AI is thinking...'):
                    results = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                    st.session_state[f"res_{t['id']}"] = results
            
            if f"res_{t['id']}" in st.session_state:
                st.write("**Choose a version:**")
                for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                    st.caption(f"Version {i+1}")
                    st.write(msg)
                    if st.button("Select this version", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
            
            t['Draft'] = st.text_area("Final Polish", value=t['Draft'], key=f"ed_{t['id']}")
            if st.button("Submit for Approval", key=f"sub_{t['id']}"):
                t['Status'] = "Pending"
                st.rerun()

# ---- PAGE: DAILY REPORT ----
elif menu == "Daily Report":
    st.title("📊 Daily Summary")
    if st.session_state.db:
        st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
    else:
        st.write("System is empty.")
