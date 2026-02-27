import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI Styling: High-End Gemini Dark ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    .stApp { background-color: #131314; color: #E3E3E3; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; border-right: 1px solid #333537; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important; color: #FFFFFF !important;
        border: 1px solid #444746 !important; border-radius: 12px !important;
    }
    div.stButton > button {
        border-radius: 24px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; font-weight: 500; border: none; padding: 0.6rem 2.5rem;
    }
    .stInfo { background-color: #041E3C !important; color: #D3E3FD !important; border: 1px solid #0842A0 !important; border-radius: 14px !important; }
    div[data-testid="stExpander"] { border-radius: 16px !important; border: 1px solid #444746 !important; background-color: #1E1F20 !important; }
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 600 !important; }
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

# --- 3. Deep Extraction API Logic ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" # Key ล่าสุด
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "gemini_final_fix"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_json = response.json()
        
        # เจาะลึกถึง 'text' ตามโครงสร้างในรูป image_1aae73.png
        # ดึง data -> outputs -> text
        raw_output = res_json.get('data', {}).get('outputs', {}).get('text', "")
        
        if not raw_output:
            return []
            
        # ล้างเครื่องหมาย \n และแยกข้อความ
        # กรองเฉพาะบรรทัดที่ขึ้นต้นด้วยตัวเลข 1-10 หรือบรรทัดที่มีข้อความ
        raw_output = str(raw_output).replace('\\n', '\n')
        lines = [line.strip() for line in raw_output.split('\n') if len(line.strip()) > 10]
        
        # ลบเลขลำดับข้างหน้าออก (เช่น "1. ", "2. ") เพื่อให้พร้อมใช้งาน
        clean_lines = [re.sub(r'^\d+\.\s*', '', line) for line in lines]
        return clean_lines
    except:
        return []

# --- 4. Logic Flow ---
if not st.session_state.logged_in:
    st.markdown("<br><h1 style='text-align: center;'>✨ Sign in to RoV Seeding</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Garena Email")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if u in st.session_state.users and st.session_state.users[u]["pass"] == p:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[u]
                    st.rerun()
                else: st.error("ข้อมูลไม่ถูกต้อง")
else:
    user = st.session_state.user_info
    st.sidebar.markdown(f"### 💎 {user['name']}")
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    menu = ["PIC Workspace", "Daily Report"]
    if user['role'] == "Admin": menu = ["Admin Control", "PIC Workspace", "Daily Report"]
    choice = st.sidebar.selectbox("Navigate", menu)

    if choice == "Admin Control":
        st.title("👨‍💻 Admin Control")
        with st.expander("Assign Task", expanded=True):
            with st.form("task_f"):
                t_topic = st.text_input("Topic")
                t_pic = st.selectbox("Assign to", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
                t_guide = st.text_area("Guideline")
                if st.form_submit_button("Deploy"):
                    st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                    st.success("Task Deployed!")

    elif choice == "PIC Workspace":
        st.title("📱 My Workspace")
        tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
        
        for t in tasks:
            with st.expander(f"📌 {t['Topic']} — {t['Status']}", expanded=True):
                st.write(f"**Guide:** {t['Guide']}")
                
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('Gemini กำลังแกะข้อความ Seeding ทั้ง 10 แบบ...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                        if res:
                            st.session_state[f"res_{t['id']}"] = res
                        else:
                            st.error("AI ไม่ส่งข้อมูล (ลองกด Publish ใน Agent แล้วรันใหม่)")

                res_key = f"res_{t['id']}"
                if res_key in st.session_state:
                    st.markdown("---")
                    for i, msg in enumerate(st.session_state[res_key]):
                        st.info(msg)
                        if st.button(f"ใช้ข้อความที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                            st.success(f"เลือกแบบที่ {i+1} แล้ว")
                
                t['Draft'] = st.text_area("Final Draft", value=t['Draft'], key=f"ed_{t['id']}", height=120)
                if st.button("Submit", key=f"sub_{t['id']}"):
                    t['Status'] = "Pending"
                    st.rerun()

    elif choice == "Daily Report":
        st.title("📊 Daily Summary")
        if st.session_state.db: st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
