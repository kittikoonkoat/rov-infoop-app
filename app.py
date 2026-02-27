import streamlit as st
import pandas as pd
import requests

# --- 1. UI Styling (Gemini Dark Mode) ---
st.set_page_config(page_title="RoV Seeding - Gemini Edition", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; border-right: 1px solid #333537; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1F20 !important; color: #E3E3E3 !important;
        border: 1px solid #444746 !important; border-radius: 18px !important;
    }
    div.stButton > button {
        border-radius: 20px; background: linear-gradient(90deg, #4285F4, #1A73E8);
        color: white; font-weight: 600; border: none; padding: 0.6rem 2rem;
    }
    div[data-testid="stExpander"] {
        border-radius: 16px !important; border: 1px solid #444746 !important;
        background-color: #1E1F20 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ข้อมูล User ---
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

# --- 3. ฟังก์ชันเรียกใช้งาน API (แก้ปัญหาข้อมูลไม่ขึ้น) ---
def call_seeding_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "QaddR42ehoje6VK9ZxITB9ZFS5C2mr1f" 
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": topic, "Guide": guide, "Persona": persona},
        "response_mode": "blocking",
        "user": "garena_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        # ปรับปรุงการดึงข้อมูล: ดึงข้อความดิบออกมาก่อน
        outputs = result.get('data', {}).get('outputs', {})
        # ลองหาจาก key 'text' หรือ 'answer' หรือดึงค่าแรกที่เจอ
        raw_text = outputs.get('text') or outputs.get('answer') or next(iter(outputs.values()), "")
        
        if not raw_text:
            return ["⚠️ AI ส่งคำตอบกลับมาเป็นค่าว่าง ลองตรวจสอบการตั้งค่า Node End ใน Agent อีกครั้งครับ"]
            
        # ถ้าเป็นข้อความยาวๆ ให้แยกเป็นบรรทัดเพื่อสร้างตัวเลือก
        lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 2]
        return lines if lines else [raw_text]
        
    except Exception as e:
        return [f"❌ เกิดข้อผิดพลาด: {str(e)}"]

# --- 4. Login ---
if not st.session_state.logged_in:
    st.title("✨ RoV Seeding Login")
    email_input = st.text_input("Garena Email")
    pass_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if email_input in st.session_state.users and st.session_state.users[email_input]["pass"] == pass_input:
            st.session_state.logged_in = True
            st.session_state.user_info = st.session_state.users[email_input]
            st.rerun()
    st.stop()

# --- 5. Main Content ---
user = st.session_state.user_info
menu = st.sidebar.selectbox("Navigate", ["Admin Control", "PIC Workspace", "Daily Report", "User Management"] if user['role'] == "Admin" else ["PIC Workspace"])

if menu == "PIC Workspace":
    st.title("📱 PIC Workspace")
    my_tasks = [t for t in st.session_state.db if t['PIC'] == user['name'] or user['role'] == "Admin"]
    
    if not my_tasks:
        st.info("ยังไม่มีงานที่ได้รับมอบหมาย")
        
    for t in my_tasks:
        with st.expander(f"📌 {t['Topic']} ({t['Status']})"):
            st.write(f"**Guide:** {t['Guide']}")
            
            # ปุ่มเรียก AI
            if st.button("✨ ให้ AI ช่วยร่างข้อความ", key=f"ai_{t['id']}"):
                with st.spinner('Gemini กำลังร่างข้อความ...'):
                    results = call_seeding_agent(t['Topic'], t['Guide'], user['name'])
                    st.session_state[f"res_{t['id']}"] = results
            
            # แสดงผลลัพธ์จาก AI
            if f"res_{t['id']}" in st.session_state:
                st.markdown("---")
                st.write("**เลือกข้อความที่ต้องการ:**")
                for i, msg in enumerate(st.session_state[f"res_{t['id']}"]):
                    st.info(msg)
                    if st.button(f"เลือกแบบที่ {i+1}", key=f"sel_{t['id']}_{i}"):
                        t['Draft'] = msg
                        st.success("เลือกข้อความแล้ว! ตรวจสอบที่ช่องด้านล่าง")
            
            t['Draft'] = st.text_area("ข้อความที่จะใช้ (แก้ไขได้)", value=t['Draft'], key=f"ed_{t['id']}")
            if st.button("ส่งให้ Admin ตรวจ", key=f"sub_{t['id']}"):
                t['Status'] = "Pending Approval"
                st.rerun()

elif menu == "Admin Control":
    st.title("👨‍💼 Admin Control")
    with st.form("task_form"):
        t_topic = st.text_input("หัวข้อ")
        t_pic = st.selectbox("มอบหมายให้", [v['name'] for v in st.session_state.users.values() if v['role']=="PIC"])
        t_guide = st.text_area("Guide")
        if st.form_submit_button("Assign Task"):
            st.session_state.db.append({"id": len(st.session_state.db)+1, "Topic": t_topic, "PIC": t_pic, "Guide": t_guide, "Status": "Waiting", "Draft": ""})
            st.success("ส่งงานสำเร็จ!")

# (ส่วนอื่นๆ ของโค้ดคงเดิม)
