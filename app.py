import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import re
import datetime

# ==========================================
# 1. การเชื่อมต่อ DATABASE
# ==========================================

def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        # แก้ปัญหา Seekable bit stream
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
            st.session_state.db = sh.worksheet("tasks").get_all_records()
            st.session_state.users_db = sh.worksheet("users").get_all_records()
            st.session_state.channels = sh.worksheet("channels").get_all_records()
            st.sidebar.success("🔄 ซิงค์ข้อมูลครบถ้วน")
        except Exception as e:
            st.error(f"⚠️ โครงสร้าง Sheets ไม่ถูกต้อง (ตรวจสอบหัวคอลัมน์): {e}")

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
    # ส่งค่า 3 ตัวแปรตรงตาม Workflow
    payload = {
        "inputs": {"Topic": str(topic), "Guide": str(guide), "Persona": str(persona)},
        "response_mode": "blocking", "user": "kittikoon_user"
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        raw_text = ""
        if 'data' in res and 'outputs' in res['data']:
            raw_text = res['data']['outputs'].get('text', "")
        # แยกเป็น 10 แบบ
        options = [l.strip() for l in re.split(r'\n|\d+\.', str(raw_text)) if len(l.strip()) > 5]
        return options[:10] if options else ["AI ยังคิดไม่ออก ลองปรับข้อมูลใน Guide/Persona นะคะ"]
    except Exception as e:
        return [f"❌ Error AI: {str(e)}"]

# ==========================================
# 3. MAIN APP LOGIC (Fix Black Screen)
# ==========================================

st.set_page_config(page_title="RoV Seeding Pro", layout="wide")

# ตรวจสอบการโหลดข้อมูลเบื้องต้น
if 'db' not in st.session_state:
    sync_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- หน้าจอ LOGIN ---
if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    col1, _ = st.columns([1, 1.5])
    with col1:
        u_email = st.text_input("Email")
        u_pass = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            if 'users_db' in st.session_state:
                user = next((x for x in st.session_state.users_db if str(x['email']) == u_email and str(x['password']) == u_pass), None)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user['role']
                    st.session_state.current_user = user['email']
                    st.rerun()
                else:
                    st.error("❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง")

# --- หน้าจอหลัง LOGIN ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    st.sidebar.write(st.session_state.current_user)
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 1. หน้าจอสำหรับ BOSS ---
    if st.session_state.user_role == "Boss":
        st.title("👨‍💼 Boss Control Panel")
        
        with st.expander("➕ มอบหมายงานใหม่"):
            with st.form("new_task"):
                t_input = st.text_input("หัวข้อคอนเทนต์ (Topic):")
                p_input = st.selectbox("Assign to Admin:", [u['email'] for u in st.session_state.users_db if u['role'] == 'Admin'])
                if st.form_submit_button("สั่งงาน"):
                    new_task = {
                        "id": len(st.session_state.db) + 1, "Topic": t_input, "PIC": p_input, "Status": "Pending",
                        "Guide": "", "Persona": "", "FB_Group": "", "Draft": "", "Date": str(datetime.date.today())
                    }
                    st.session_state.db.append(new_task)
                    save_to_sheets(st.session_state.db)
                    st.rerun()

        st.subheader("🔍 งานที่รออนุมัติ (Reviewing)")
        for t in [x for x in st.session_state.db if x['Status'] == "Reviewing"]:
            with st.expander(f"📋 ตรวจงาน: {t['Topic']} (โดย {t['PIC']})"):
                st.write(f"**กลุ่ม FB:** {t.get('FB_Group', 'N/A')}")
                st.info(f"**Draft:** {t['Draft']}")
                c1, c2 = st.columns(2)
                if c1.button("✅ Approve", key=f"ap_{t['id']}", use_container_width=True):
                    t['Status'] = "Approved"; save_to_sheets(st.session_state.db); st.rerun()
                if c2.button("❌ Reject", key=f"rj_{t['id']}", use_container_width=True):
                    t['Status'] = "Pending"; save_to_sheets(st.session_state.db); st.rerun()

    # --- 2. หน้าจอสำหรับ ADMIN ---
    elif st.session_state.user_role == "Admin":
        st.title("👩‍💻 My Assigned Tasks")
        fb_group_options = [c['group_name'] for c in st.session_state.get('channels', [])]

        for t in [x for x in st.session_state.db if x['PIC'] == st.session_state.current_user and x['Status'] != "Approved"]:
            with st.expander(f"📌 {t['Topic']} | {t['Status']}", expanded=True):
                st.write("**เลือกกลุ่ม FB:**")
                t['FB_Group'] = st.selectbox("Group:", options=fb_group_options, index=fb_group_options.index(t['FB_Group']) if t.get('FB_Group') in fb_group_options else 0, key=f"fb_{t['id']}", label_visibility="collapsed")
                
                col1, col2 = st.columns(2)
                with col1:
                    t['Guide'] = st.text_area("แนวทาง (Guide):", value=t.get('Guide', ""), key=f"g_{t['id']}")
                with col2:
                    t['Persona'] = st.text_area("บุคลิก AI (Persona):", value=t.get('Persona', "") or "แอดมินกะเทย RoV", key=f"p_{t['id']}")

                if st.button("✨ Draft with AI (10 แบบ)", key=f"ai_{t['id']}"):
                    st.session_state[f"opts_{t['id']}"] = call_ai_agent(t['Topic'], t['Guide'], t['Persona'])

                if f"opts_{t['id']}" in st.session_state:
                    for i, msg in enumerate(st.session_state[f"opts_{t['id']}"]):
                        if st.button(f"เลือกแบบที่ {i+1}: {msg[:60]}...", key=f"s_{t['id']}_{i}", use_container_width=True):
                            t['Draft'] = msg; st.rerun()

                t['Draft'] = st.text_area("ร่างสุดท้าย:", value=t.get('Draft', ""), key=f"dr_{t['id']}", height=150)
                if st.button("ส่งงานให้บอสตรวจ", key=f"sub_{t['id']}", use_container_width=True):
                    t['Status'] = "Reviewing"; save_to_sheets(st.session_state.db); st.rerun()
