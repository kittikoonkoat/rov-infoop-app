import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import re

# ==========================================
# 1. GOOGLE SHEETS CONNECTION SETUP
# ==========================================

def init_connection():
    """เชื่อมต่อกับ Google Sheets โดยใช้ค่าจาก Streamlit Secrets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # ใช้ข้อมูลจากไฟล์ JSON ล่าสุดที่คุณอัปโหลด
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

def sync_data():
    """ดึงข้อมูลล่าสุดจาก Sheets"""
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.session_state.channels = sh.worksheet("channels").get_all_records()
            st.sidebar.success("🔄 ข้อมูลซิงค์ล่าสุดแล้ว")
        except Exception as e:
            st.error(f"ไม่พบ Worksheet: {e}")

def save_data(worksheet_name, data_list):
    """บันทึกข้อมูลลง Sheets"""
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet(worksheet_name)
            ws.clear()
            if data_list:
                df = pd.DataFrame(data_list)
                ws.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            st.error(f"บันทึกไม่สำเร็จ: {e}")

# ==========================================
# 2. AI AGENT CONNECTOR (ปรับปรุงการแกะข้อมูล)
# ==========================================

def call_ai_agent(topic, guide):
    """เรียกใช้ AI และจัดการผลลัพธ์ให้ได้ 10 ตัวเลือก"""
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": "กะเทย เล่น rov มานาน พูดจาจิกกัดแต่น่ารัก ร่างข้อความมา 10 แบบ ห้ามใส่เลขข้อ ให้ขึ้นบรรทัดใหม่แยกกันชัดเจน"
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # เจาะลึกโครงสร้าง JSON ของ INSEA AI
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'text' in res:
            raw_text = res.get('text', "")
        
        # แยกข้อความ (Split) ด้วยการขึ้นบรรทัดใหม่
        options = [l.strip() for l in str(raw_text).split('\n') if len(l.strip()) > 5]
        
        # หาก AI ส่งมาเป็นก้อนเดียว ให้ลองแยกด้วยเลขข้อ
        if len(options) < 2:
            options = [l.strip() for l in re.split(r'\d+\.', str(raw_text)) if len(l.strip()) > 5]

        return options[:10] if options else ["AI ยังคิดไม่ออก ลองตรวจสอบ Guideline ใน Sheets นะคะ"]
        
    except Exception as e:
        return [f"❌ Error: {str(e)}"]

# ==========================================
# 3. UI INITIALIZATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ==========================================
# 4. LOGIN & MAIN APP
# ==========================================

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    # ตรวจสอบ Error จากภาพ
    if 'gcp_service_account' not in st.secrets:
        st.error("กรุณาตั้งค่า gcp_service_account ใน Streamlit Secrets ก่อนครับ")
    
    col1, _ = st.columns([1, 1.5])
    with col1:
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            user = next((x for x in st.session_state.users_db if str(x['email']) == u_email and str(x['password']) == u_pass), None)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.current_user = user['email']
                st.rerun()
            else:
                st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
else:
    # --- เมนู ADMIN ---
    st.sidebar.title(f"👤 {st.session_state.current_user}")
    menu = st.sidebar.radio("เมนูแอดมิน:", ["งานที่ได้รับมอบหมาย", "ส่งยอดประจำวัน"])
    
    if menu == "งานที่ได้รับมอบหมาย":
        st.title("📥 My Assigned Tasks")
        my_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]
        
        for t in my_jobs:
            with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                if t['Status'] == "Pending":
                    channel_names = [c['group_name'] for c in st.session_state.channels]
                    selected_g = st.selectbox("เลือกกลุ่ม FB:", channel_names, key=f"g_{t['id']}")
                    
                    # ปุ่ม AI แบบ 10 แบบ
                    if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_{t['id']}"):
                        with st.spinner("กะเทยกำลังคิดให้ 10 แบบ..."):
                            st.session_state[f"ai_options_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'])
                    
                    # ส่วนแสดงปุ่มเลือกแบบ
                    if f"ai_options_{t['id']}" in st.session_state:
                        st.write("🤖 เลือกข้อความที่โดนใจแอดมิน:")
                        opts = st.session_state[f"ai_options_{t['id']}"]
                        for i, msg in enumerate(opts):
                            if st.button(f"✅ แบบที่ {i+1}: {msg[:60]}...", key=f"btn_{t['id']}_{i}"):
                                t['Draft'] = msg
                                st.rerun()
                    
                    t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t['Draft'], key=f"ed_{t['id']}", height=150)
                    if st.button("ส่งให้หัวหน้าตรวจ", key=f"sub_{t['id']}", use_container_width=True):
                        t['Status'] = "Reviewing"
                        save_data("tasks", st.session_state.db)
                        st.rerun()
                
                elif t['Status'] == "Approved":
                    st.success("✅ หัวหน้าอนุมัติแล้ว!")
                    st.code(t['Draft'])

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
