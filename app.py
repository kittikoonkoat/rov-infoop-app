import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. GOOGLE SHEETS CONNECTION
# ==========================================

def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # ดึงจาก Secrets ที่เราคุยกันเรื่อง \n
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"❌ การเชื่อมต่อล้มเหลว: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.sidebar.success("🔄 ข้อมูลซิงค์สำเร็จ")
        except Exception as e:
            st.error(f"ไม่พบหน้าข้อมูล: {e}")

def save_to_sheets(data_list):
    sh = init_connection()
    if sh:
        ws = sh.worksheet("tasks")
        ws.clear()
        df = pd.DataFrame(data_list)
        ws.update([df.columns.values.tolist()] + df.values.tolist())

# ==========================================
# 2. AI WORKFLOW CONNECTOR (3 Inputs)
# ==========================================

def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # ส่งค่าครบ 3 ตัวแปรสอดคล้องกับ Workflow
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": str(persona)
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # แกะข้อความจากผลลัพธ์ AI
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
            
        # แยกเป็น 10 ข้อความย่อย
        options = [l.strip() for l in re.split(r'\n|\d+\.', str(raw_text)) if len(l.strip()) > 5]
        return options[:10] if options else ["AI คิดไม่ออก ลองปรับ Guide/Persona นะคะ"]
    except Exception as e:
        return [f"❌ Error AI: {str(e)}"]

# ==========================================
# 3. UI APPLICATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state:
    sync_data()

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    u_email = st.text_input("Email")
    u_pass = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user = next((x for x in st.session_state.users_db if x['email'] == u_email and str(x['password']) == u_pass), None)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_role = user['role']
            st.session_state.current_user = user['email']
            st.rerun()
        else:
            st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

# --- MAIN DASHBOARD ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    st.sidebar.write(st.session_state.current_user)

    # 1. หน้าจอสำหรับ BOSS (สั่งงาน)
    if st.session_state.user_role == "Boss":
        st.title("👨‍💼 Boss Assignment Panel")
        with st.form("add_task"):
            st.subheader("มอบหมายงานใหม่")
            topic = st.text_input("หัวข้อคอนเทนต์ (Topic):", placeholder="เช่น รีวิวสกินใหม่ Nakroth")
            pic = st.selectbox("เลือก Admin ที่จะรับผิดชอบ:", [u['email'] for u in st.session_state.users_db if u['role'] == 'Admin'])
            if st.form_submit_button("ส่งงานให้ Admin"):
                new_id = len(st.session_state.db) + 1
                new_task = {
                    "id": new_id, "Topic": topic, "PIC": pic, "Status": "Pending",
                    "Guide": "", "Persona": "", "Draft": "", "Date": str(datetime.date.today())
                }
                st.session_state.db.append(new_task)
                save_to_sheets(st.session_state.db)
                st.success(f"ส่งงานหัวข้อ '{topic}' ให้ {pic} เรียบร้อย!")

    # 2. หน้าจอสำหรับ ADMIN (ใส่ Guide, Persona และเรียก AI)
    elif st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]

        for t in my_tasks:
            with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                st.info(f"**Topic จาก Boss:** {t['Topic']}")
                
                # Admin ใส่ Guide และ Persona เอง
                col1, col2 = st.columns(2)
                with col1:
                    t['Guide'] = st.text_area("แนวทาง (Guide):", value=t['Guide'], key=f"g_{t['id']}", placeholder="เน้นความตลก, เน้นข้อมูลแน่นๆ")
                with col2:
                    t['Persona'] = st.text_area("บุคลิก AI (Persona):", value=t['Persona'] if t['Persona'] else "กะเทยแอดมินเพจ RoV", key=f"p_{t['id']}")

                # ปุ่ม Draft AI ที่สอดคล้องกับ Workflow
                if st.button("✨ Draft with AI (10 แบบ)", key=f"btn_{t['id']}"):
                    with st.spinner("กำลังคุยกับ AI..."):
                        # ส่ง 3 ค่าเข้า API
                        st.session_state[f"opts_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'], t['Persona'])
                
                # แสดงผลลัพธ์ 10 แบบ
                if f"opts_{t['id']}" in st.session_state:
                    st.write("🤖 **เลือกข้อความที่ต้องการ:**")
                    for i, msg in enumerate(st.session_state[f"opts_{t['id']}"]):
                        if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"sel_{t['id']}_{i}", use_container_width=True):
                            t['Draft'] = msg
                            st.rerun()

                t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t['Draft'], key=f"dr_{t['id']}", height=150)
                
                if st.button("ส่งให้ Boss ตรวจ", key=f"sub_{t['id']}"):
                    t['Status'] = "Reviewing"
                    save_to_sheets(st.session_state.db)
                    st.success("ส่งงานสำเร็จ!")
                    st.rerun()

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
