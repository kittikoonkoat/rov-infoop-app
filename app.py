import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import json

# ==========================================
# 1. การเชื่อมต่อ GOOGLE SHEETS (แก้ไขจุดที่เกิด Error)
# ==========================================

def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # ดึงข้อมูลจาก Secrets ที่คุณตั้งค่าไว้
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
            
        # จัดการ \n ใน private_key ให้ถูกประเภทข้อมูล
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        # ใช้ google.oauth2.service_account แทนเพื่อเลี่ยง Error 'seekable bit stream'
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        # แสดง Error บนหน้าจอ
        st.error(f"❌ เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.session_state.channels = sh.worksheet("channels").get_all_records()
            st.sidebar.success("🔄 ซิงค์ข้อมูลสำเร็จ")
        except Exception as e:
            st.error(f"ไม่พบ Worksheet: {e}")

def save_data(worksheet_name, data_list):
    sh = init_connection()
    if sh:
        try:
            ws = sh.worksheet(worksheet_name)
            ws.clear()
            if data_list:
                df = pd.DataFrame(data_list)
                ws.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            st.error(f"บันทึกข้อมูลล้มเหลว: {e}")

# ==========================================
# 2. ระบบ AI (แก้ปัญหาคิดข้อความไม่ออก)
# ==========================================

def call_ai_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # บังคับให้ AI ตอบกลับมาในรูปแบบที่คั่นด้วยสัญลักษณ์ชัดเจน
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": "คุณคือกะเทยแอดมินเพจ RoV ร่างข้อความมา 10 แบบ โดยแต่ละแบบให้คั่นด้วยเครื่องหมาย ### และห้ามใส่เลขข้อ"
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # 1. พยายามดึงข้อความจากหลายๆ Key ที่ API อาจจะส่งมา
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'text' in res:
            raw_text = res.get('text', "")
        elif 'answer' in res:
            raw_text = res.get('answer', "")
            
        if not raw_text:
            return [f"AI ไม่ส่งข้อมูลกลับมา (Response: {str(res)[:100]})"]

        # 2. ระบบแยกข้อความ (Splitting Logic)
        # แยกด้วย ### ตามที่สั่งใน Persona หรือแยกด้วยการขึ้นบรรทัดใหม่
        options = []
        if "###" in raw_text:
            options = [opt.strip() for opt in raw_text.split("###") if len(opt.strip()) > 5]
        else:
            # กรณี AI ไม่ทำตามสั่ง ให้แยกด้วยบรรทัด
            options = [opt.strip() for opt in re.split(r'\n+', raw_text) if len(opt.strip()) > 5]

        # 3. ส่งคืนค่า 10 ตัวเลือก
        return options[:10] if options else ["AI คิดข้อความไม่ออกจริงๆ ค่ะ ลองตรวจสอบ Guideline ใน Sheets นะคะ"]
        
    except Exception as e:
        return [f"❌ เกิดข้อผิดพลาดทางเทคนิค: {str(e)}"]

# ==========================================
# 3. UI APPLICATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Management", layout="wide")

if 'db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    col1, _ = st.columns([1, 1.5])
    with col1:
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            # ตรวจสอบว่าซิงค์ข้อมูลผู้ใช้มาหรือยัง
            if 'users_db' in st.session_state:
                user = next((x for x in st.session_state.users_db if str(x['email']) == u_email and str(x['password']) == u_pass), None)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user['role']
                    st.session_state.current_user = user['email']
                    st.rerun()
                else:
                    st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
else:
    st.sidebar.title(f"👤 {st.session_state.current_user}")
    
    if st.session_state.user_role == "Admin":
        st.title("📥 งานที่ได้รับมอบหมาย")
        my_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]
        
        for t in my_jobs:
            with st.expander(f"📌 {t['Topic']} | {t['Status']}", expanded=True):
                if t['Status'] == "Pending":
                    # ปุ่ม Draft AI (10 แบบ)
                    if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_{t['id']}"):
                        with st.spinner("กะเทยกำลังคิดข้อความให้เลือก..."):
                            st.session_state[f"ai_options_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'])
                    
                    # แสดงผลตัวเลือกปุ่ม 1-10
                    if f"ai_options_{t['id']}" in st.session_state:
                        st.info("🤖 เลือกข้อความที่ต้องการ:")
                        opts = st.session_state[f"ai_options_{t['id']}"]
                        for i, msg in enumerate(opts):
                            if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"btn_{t['id']}_{i}", use_container_width=True):
                                t['Draft'] = msg
                                st.rerun()
                    
                    t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t['Draft'], key=f"ed_{t['id']}", height=150)
                    if st.button("ส่งงานให้หัวหน้าตรวจ", key=f"sub_{t['id']}", use_container_width=True):
                        t['Status'] = "Reviewing"
                        save_data("tasks", st.session_state.db)
                        st.rerun()
                
                elif t['Status'] == "Approved":
                    st.success("✅ อนุมัติแล้ว! คัดลอกไปโพสต์ได้เลย")
                    st.code(t['Draft'])

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
