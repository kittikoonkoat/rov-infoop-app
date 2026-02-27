import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import re
import json

# ==========================================
# 1. GOOGLE SHEETS CONNECTION (ใช้ข้อมูลจาก JSON ที่คุณให้มา)
# ==========================================

def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        # ใช้ข้อมูลจาก rov-ya-mo-02665ab0b48a.json
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

# ==========================================
# 2. AI CONNECTOR (แก้ไขให้ดึง 10 ข้อความแน่นอน)
# ==========================================

def call_ai_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "inputs": {
            "Topic": str(topic), 
            "Guide": str(guide), 
            "Persona": "คุณคือแอดมินเพจเกม RoV ที่เป็นกะเทย ร่างข้อความมาให้เลือก 10 แบบ โดยแต่ละแบบให้ขึ้นบรรทัดใหม่ ห้ามมีเลขข้อ"
        },
        "response_mode": "blocking", 
        "user": "kittikoon_user"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # ดึงข้อความดิบ (Raw Text)
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        elif 'text' in res:
            raw_text = res.get('text', "")
        else:
            # หากหา Key ไม่เจอ ให้ดึง JSON ทั้งหมดมาดู (Debug)
            raw_text = str(res)

        # การแยกข้อความ: ใช้ Regex ที่รองรับหลายรูปแบบ
        # แยกด้วยการขึ้นบรรทัดใหม่ (\n) หรือกรณีที่ AI ใส่เลขข้อมา (1., 2.)
        options = [l.strip() for l in re.split(r'\n|\d+\.', str(raw_text)) if len(l.strip()) > 5]
        
        # ถ้ายังแยกไม่ได้ 10 แบบ ให้ลองแบ่งด้วยเครื่องหมายคำพูด หรือสัญลักษณ์อื่นๆ
        if len(options) < 2:
            options = [l.strip() for l in str(raw_text).split('\"') if len(l.strip()) > 5]

        return options[:10] if options else [f"ขออภัยค่ะ AI ตอบกลับมาในรูปแบบที่อ่านไม่ได้: {str(raw_text)[:100]}"]
        
    except Exception as e:
        return [f"❌ เกิดข้อผิดพลาดทางเทคนิค: {str(e)}"]

# ==========================================
# 3. UI ADMIN (ส่วนที่มีปัญหาในภาพ image_d7fe5c.png)
# ==========================================

# ... (ส่วน Login และการดึงข้อมูล sync_data เดิม) ...

if 'logged_in' in st.session_state and st.session_state.logged_in:
    if st.session_state.user_role == "Admin":
        st.title("📥 My Assigned Tasks")
        my_jobs = [t for t in st.session_state.db if t['PIC'] == st.session_state.current_user]
        
        for t in my_jobs:
            with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                if t['Status'] == "Pending":
                    # --- ปุ่ม Draft AI ---
                    if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_btn_{t['id']}"):
                        with st.spinner("กะเทยกำลังปั่นงานให้ 10 แบบนะคะ..."):
                            # เก็บผลลัพธ์ลงใน Session State แยกตาม ID งาน
                            st.session_state[f"draft_options_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'])
                    
                    # --- ส่วนแสดงปุ่มตัวเลือก ---
                    # ตรวจสอบว่าใน Session State มีข้อมูลของงาน ID นี้หรือไม่
                    option_key = f"draft_options_{t['id']}"
                    if option_key in st.session_state:
                        st.write("🤖 **เลือกข้อความที่โดนใจแอดมิน:**")
                        current_options = st.session_state[option_key]
                        
                        # สร้างปุ่ม 10 ปุ่ม
                        for i, msg in enumerate(current_options):
                            # ใช้ Button แบบเต็มความกว้างเพื่อให้กดง่าย
                            if st.button(f"แบบที่ {i+1}: {msg[:70]}...", key=f"sel_{t['id']}_{i}", use_container_width=True):
                                t['Draft'] = msg
                                # ล้างตัวเลือกทิ้งหลังจากเลือกแล้ว (ถ้าต้องการ) หรือเก็บไว้ก็ได้
                                st.rerun()
                    
                    # ช่องแก้ไขข้อความ
                    t['Draft'] = st.text_area("ร่างข้อความสุดท้าย (แก้ไขเพิ่มเติมได้):", value=t['Draft'], key=f"area_{t['id']}", height=150)
                    
                    if st.button("ส่งให้หัวหน้าตรวจ", key=f"sub_{t['id']}", use_container_width=True):
                        t['Status'] = "Reviewing"
                        # save_data(st.session_state.db)
                        st.success("ส่งงานสำเร็จ!")
                        st.rerun()
