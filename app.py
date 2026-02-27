import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import re

# ==========================================
# 1. การเชื่อมต่อ GOOGLE SHEETS
# ==========================================

def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # ดึงข้อมูลจาก Secrets ที่ตั้งค่าไว้ตามไฟล์ JSON
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"❌ เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.session_state.channels = sh.worksheet("channels").get_all_records()
            st.sidebar.success("🔄 ข้อมูลอัปเดตแล้ว")
        except Exception as e:
            st.error(f"ไม่พบแผ่นงาน: {e}")

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
            st.error(f"บันทึกข้อมูลไม่สำเร็จ: {e}")

# ==========================================
# 2. ระบบ AI ดึง 10 ตัวเลือก (ปรับปรุงการแยกบรรทัด)
# ==========================================

def call_ai_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": "แอดมินกะเทย RoV พูดจาจิกกัดแต่น่ารัก ร่างข้อความมา 10 แบบ ห้ามใส่เลขข้อ ให้ขึ้นบรรทัดใหม่แยกกันชัดเจน"
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # ดึงข้อความดิบจากโครงสร้าง JSON ของ INSEA AI
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'text' in res:
            raw_text = res.get('text', "")
            
        # ใช้ Regex แยกบรรทัดให้แม่นยำขึ้น (รองรับทั้ง \n และเลขข้อที่ AI อาจแอบใส่มา)
        options = [l.strip() for l in re.split(r'\n|\d+\.', str(raw_text)) if len(l.strip()) > 5]
        
        return options[:10] if options else ["AI ส่งข้อมูลมาผิดรูปแบบ ลองกดใหม่อีกครั้งนะคะ"]
        
    except Exception as e:
        return [f"❌ Error AI: {str(e)}"]

# ==========================================
# 3. UI และระบบจัดการงาน
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
    
    # เมนูสำหรับ ADMIN
    if st.session_state.user_role == "Admin":
        menu = st.sidebar.radio("เมนู:", ["งานที่ได้รับมอบหมาย", "ส่งยอดประจำวัน"])
        
        if menu == "งานที่ได้รับมอบหมาย":
            st.title("📥 My Assigned Tasks")
            my_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]
            
            for t in my_jobs:
                with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                    if t['Status'] == "Pending":
                        # เลือกกลุ่ม FB
                        channel_names = [c['group_name'] for c in st.session_state.channels]
                        selected_g = st.selectbox("เลือกกลุ่ม FB:", channel_names, key=f"g_{t['id']}")
                        
                        # ปุ่มเรียก AI (แก้ไขสถานะให้ไม่หายเมื่อกดเลือก)
                        if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_{t['id']}"):
                            with st.spinner("กะเทยกำลังร่างบทให้ 10 แบบ..."):
                                st.session_state[f"ai_options_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'])
                        
                        # แสดงผลปุ่มเลือก 10 แบบ
                        if f"ai_options_{t['id']}" in st.session_state:
                            st.write("🤖 **เลือกข้อความที่โดนใจ:**")
                            opts = st.session_state[f"ai_options_{t['id']}"]
                            for i, msg in enumerate(opts):
                                if st.button(f"✅ แบบที่ {i+1}: {msg[:60]}...", key=f"btn_{t['id']}_{i}", use_container_width=True):
                                    t['Draft'] = msg
                                    st.rerun()
                        
                        t['Draft'] = st.text_area("ร่างข้อความสุดท้าย:", value=t['Draft'], key=f"ed_{t['id']}", height=150)
                        if st.button("ส่งให้หัวหน้าตรวจ", key=f"sub_{t['id']}", use_container_width=True):
                            t['Status'] = "Reviewing"
                            save_data("tasks", st.session_state.db)
                            st.rerun()
                    
                    elif t['Status'] == "Approved":
                        st.success("✅ อนุมัติแล้ว! คัดลอกไปโพสต์ได้เลย")
                        st.code(t['Draft'])

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
