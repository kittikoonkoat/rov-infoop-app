import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. การเชื่อมต่อและดึงข้อมูลจากหลาย Tab
# ==========================================

def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds).open("RoV_Seeding_DB")
    except Exception as e:
        st.error(f"❌ เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

def sync_data():
    sh = init_connection()
    if sh:
        try:
            # ดึงข้อมูลจาก Tab ต่างๆ
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            
            # ดึงรายชื่อกลุ่ม FB จาก Tab 'channels'
            st.session_state.channels = sh.worksheet("channels").get_all_records()
            
            st.sidebar.success("🔄 ซิงค์ข้อมูลครบถ้วน")
        except Exception as e:
            st.error(f"Error ซิงค์ข้อมูล: {e}")

def save_to_sheets(data_list):
    sh = init_connection()
    if sh:
        ws = sh.worksheet("tasks")
        ws.clear()
        df = pd.DataFrame(data_list)
        ws.update([df.columns.values.tolist()] + df.values.tolist())

# ==========================================
# 2. AI WORKFLOW CONNECTOR
# ==========================================

def call_ai_agent(topic, guide, persona):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH" 
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "inputs": {"Topic": str(topic), "Guide": str(guide), "Persona": str(persona)},
        "response_mode": "blocking", "user": "kittikoon_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        raw_text = res['data']['outputs'].get('text', "") if 'data' in res else ""
        options = [l.strip() for l in re.split(r'\n|\d+\.', str(raw_text)) if len(l.strip()) > 5]
        return options[:10]
    except Exception as e:
        return [f"❌ Error AI: {str(e)}"]

# ==========================================
# 3. UI APPLICATION
# ==========================================

st.set_page_config(page_title="RoV Seeding Pro", layout="wide")

if 'db' not in st.session_state:
    sync_data()

# (ส่วน Login คงเดิม...)

if st.session_state.get('logged_in'):
    
    # --- หน้าจอสำหรับ BOSS (คงเดิม) ---
    if st.session_state.user_role == "Boss":
        st.title("👨‍💼 Boss Control Panel")
        # ส่วนสั่งงานและตรวจงาน...

    # --- หน้าจอสำหรับ ADMIN (ดึงข้อมูลกลุ่มจาก channels) ---
    elif st.session_state.user_role == "Admin":
        st.title("👩‍💻 My Assigned Tasks")
        
        # เตรียมรายชื่อกลุ่มจาก Database
        # ดึงเฉพาะคอลัมน์ group_name มาแสดง
        fb_group_options = [c['group_name'] for c in st.session_state.channels] if 'channels' in st.session_state else ["No Group Found"]

        for t in [x for x in st.session_state.db if x['PIC'] == st.session_state.current_user and x['Status'] != "Approved"]:
            with st.expander(f"📌 {t['Topic']} | {t['Status']}", expanded=True):
                
                # 1. ระบบเลือกกลุ่ม FB ที่ดึงข้อมูลมาจาก Database
                st.write("**เลือกกลุ่ม FB (จากฐานข้อมูล):**")
                selected_group = st.selectbox(
                    "Select Group:", 
                    options=fb_group_options,
                    index=fb_group_options.index(t['FB_Group']) if t.get('FB_Group') in fb_group_options else 0,
                    key=f"fb_{t['id']}",
                    label_visibility="collapsed"
                )
                t['FB_Group'] = selected_group # บันทึกค่าลงใน Task

                # แสดง URL ของกลุ่มให้ Admin เห็นด้วยเพื่อความสะดวก
                current_url = next((c['group_url'] for c in st.session_state.channels if c['group_name'] == selected_group), "")
                if current_url:
                    st.caption(f"🔗 [ไปยังกลุ่มนี้]({current_url})")

                col1, col2 = st.columns(2)
                with col1:
                    t['Guide'] = st.text_area("แนวทาง (Guide):", value=t.get('Guide', ""), key=f"g_{t['id']}")
                with col2:
                    t['Persona'] = st.text_area("บุคลิก AI (Persona):", value=t.get('Persona', "") or "แอดมินกะเทย RoV", key=f"p_{t['id']}")

                # 2. ปุ่ม Draft AI (Topic, Guide, Persona)
                if st.button("✨ Draft with AI (10 แบบ)", key=f"btn_{t['id']}"):
                    with st.spinner("กำลังคุยกับ AI..."):
                        st.session_state[f"opts_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'], t['Persona'])
                
                # 3. เลือกข้อความ
                if f"opts_{t['id']}" in st.session_state:
                    st.write("🤖 **เลือกข้อความที่ต้องการ:**")
                    for i, msg in enumerate(st.session_state[f"opts_{t['id']}"]):
                        if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"sel_{t['id']}_{i}", use_container_width=True):
                            t['Draft'] = msg
                            st.rerun()

                t['Draft'] = st.text_area("ร่างสุดท้าย:", value=t.get('Draft', ""), key=f"dr_{t['id']}", height=150)
                
                if st.button("ส่งงานตรวจ", key=f"sub_{t['id']}"):
                    t['Status'] = "Reviewing"
                    save_to_sheets(st.session_state.db)
                    st.success("ส่งงานสำเร็จ!")
                    st.rerun()

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
