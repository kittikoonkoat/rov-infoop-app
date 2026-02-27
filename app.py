import streamlit as st
import pandas as pd
import requests
import json

# --- 1. UI Styling: High-End Gemini Dark ---
st.set_page_config(page_title="RoV Seeding Portal", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    .stApp { background-color: #131314; color: #E3E3E3; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Sidebar Luxury */
    [data-testid="stSidebar"] {
        background-color: #1E1F20 !important;
        border-right: 1px solid #333537;
    }

    /* Input & Text Area */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important;
        color: #FFFFFF !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
    }

    /* Gemini Gradient Button */
    div.stButton > button {
        border-radius: 24px;
        background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.6rem 2.5rem;
    }
    
    /* AI Result Box - High Visibility */
    .stInfo {
        background-color: #041E3C !important;
        color: #D3E3FD !important;
        border: 1px solid #0842A0 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }

    /* Clean Expander */
    div[data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
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

# --- 3. Robust AI Connector ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "gemini_final_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res_data = response.json()
        
        # ค้นหาข้อความแบบครอบจักรวาล (เจาะจง 'text' ตามภาพ image_1b96d8.png)
        outputs = res_data.get('data', {}).get('outputs', {})
        raw_text = outputs.get('text') or outputs.get('answer') or next(iter(outputs.values()), "")
        
        if not raw_text:
            return []
            
        # แยกข้อความ 10 บรรทัด
        return [line.strip() for line in str(raw_text).split('\n') if len(line.strip()) > 3]
    except Exception as e:
        return []

# --- 4. Login System ---
def login_screen():
    st.markdown("<br><h1 style='text-align: center;'>✨ RoV Seeding Portal</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Garena Email")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if u in st.session_state.users and st.session_state.users[u]["pass"] == p:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.users[u]
                    st.rerun()
                else:
                    st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

if not st.session_state.logged_in:
    login_screen()
else:
    # --- 5. Main App ---
    user = st.session_state.user_info
    st.sidebar.markdown(f"### 💎 {user['name']}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    menu = ["PIC Workspace", "Daily Report"]
    if user['role'] == "Admin": menu = ["Admin Control", "PIC Workspace", "Daily Report"]
    choice = st.sidebar.selectbox("เมนู", menu)

    if choice == "Admin Control":
        st.title("👨‍💻 Admin Control")
        with st.expander("Assign New Task"):
            with st.form("task_f"):
                t_topic = st.text_input("Topic")
                t_pic = st.selectbox("Assign to", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
                t_guide = st.text_area("Guideline")
                if st.form_submit_button("Deploy"):
                    st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
                    st.success("มอบหมายงานสำเร็จ")

    elif choice == "PIC Workspace":
        st.title("📱 My Workspace")
        tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
        if not tasks: st.info("ยังไม่มีงานในรายการ")
        for t in tasks:
            with st.expander(f"📌 {t['Topic']} - {t['Status']}"):
                st.write(f"**Guide:** {t['Guide']}")
                if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                    with st.spinner('Gemini กำลังร่างข้อความ...'):
                        res = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                        if res: st.session_state[f"res_{t['id']}"] = res
                        else: st.warning("AI ไม่ส่งข้อมูลกลับมา กรุณากดปุ่ม Publish ในหน้า Agent (Insea) แล้วลองอีกครั้ง")

                r_key = f"res_{t['id']}"
                if r_key in st.session_state:
                    for i, msg in enumerate(st.session_state[r_key]):
                        st.info(msg)
                        if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                            t['Draft'] = msg
                
                t['Draft'] = st.text_area("Final Draft", value=t['Draft'], key=f"ed_{t['id']}")
                if st.button("Submit", key=f"sub_{t['id']}"):
                    t['Status'] = "Pending"
                    st.rerun()

    elif choice == "Daily Report":
        st.title("📊 Summary")
        if st.session_state.db: st.dataframe(pd.DataFrame(st.session_state.db), use_container_width=True)
