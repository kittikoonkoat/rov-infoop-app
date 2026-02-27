import streamlit as st
import pandas as pd
import requests
import re

# --- 1. UI & Config ---
st.set_page_config(page_title="RoV Seeding Management", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1E1F20 !important; }
    div.stButton > button { border-radius: 24px; font-weight: 500; }
    .status-badge { padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Database & State (จำลอง) ---
if 'db' not in st.session_state:
    # เพิ่มฟิลด์: PIC (คนรับงาน), FB_Group (กลุ่ม), Status (สถานะ Approval), Counts (ยอดปิดวัน)
    st.session_state.db = [
        {"id": 1, "Topic": "Dyadia Buff", "Guide": "อีดอกมาแล้วบัฟเลย เลิศ", "PIC": "Admin_A", "FB_Group": "", "Draft": "", "Status": "Pending", "Post_Count": 0, "Comment_Count": 0}
    ]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None # 'Boss' หรือ 'Admin'
    st.session_state.username = ""

# --- 3. API Connector ---
def call_seeding_agent(topic, guide):
    api_url = "https://ai.insea.io/api/workflows/15905/run"
    api_key = "cqfxerDagpPV70dwoMQeDSKC9iwCY1EH"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"Topic": str(topic), "Guide": str(guide), "Persona": "กะเทย เล่น rov มานาน", "response_mode": "blocking", "user": "gemini_system"}
    try:
        res = requests.post(api_url, json=payload, headers=headers, timeout=60).json()
        raw = res.get('data', {}).get('outputs', {}).get('text', "")
        if not raw: raw = res.get('text', "")
        lines = [l.strip() for l in str(raw).split('\n') if len(l.strip()) > 5]
        return [re.sub(r'^\d+[\.\:]\s*', '', l) for l in lines]
    except: return []

# --- 4. Login System ---
if not st.session_state.logged_in:
    st.title("💎 RoV Seeding Portal")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Sign In", disabled=not (u and p)):
        if u == "kittikoon.k" and p == "boss123":
            st.session_state.logged_in, st.session_state.user_role, st.session_state.username = True, "Boss", "คุณกิตติคุณ"
            st.rerun()
        elif u.startswith("admin") and p == "garena123":
            st.session_state.logged_in, st.session_state.user_role, st.session_state.username = True, "Admin", u
            st.rerun()
        else: st.error("ข้อมูลไม่ถูกต้อง")
else:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"Role: **{st.session_state.user_role}**")
    
    # --- 5. FLOW: BOSS (หัวหน้ากำหนดงาน & Approve) ---
    if st.session_state.user_role == "Boss":
        menu = st.sidebar.radio("เมนูหัวหน้า:", ["กำหนดงานใหม่", "ตรวจงาน (Approval)", "สรุปรายงานประจำวัน"])
        
        if menu == "กำหนดงานใหม่":
            st.title("🎯 Assign New Task")
            with st.container(border=True):
                nt = st.text_input("หัวข้อ (Topic)")
                ng = st.text_area("แนวทาง (Guideline)")
                np = st.selectbox("มอบหมายให้ (PIC)", ["Admin_A", "Admin_B", "Admin_C"])
                if st.button("Deploy Task", disabled=not (nt and ng)):
                    new_id = len(st.session_state.db) + 1
                    st.session_state.db.append({"id": new_id, "Topic": nt, "Guide": ng, "PIC": np, "FB_Group": "", "Draft": "", "Status": "Pending", "Post_Count": 0, "Comment_Count": 0})
                    st.success(f"จ่ายงานให้ {np} เรียบร้อย!")

        elif menu == "ตรวจงาน (Approval)":
            st.title("👀 Waiting for Approval")
            # กรองเฉพาะงานที่แอดมินส่งมา (Status: Reviewing)
            review_list = [t for t in st.session_state.db if t['Status'] == "Reviewing"]
            if not review_list: st.info("ยังไม่มีงานที่รอการอนุมัติ")
            for t in review_list:
                with st.expander(f"📌 {t['Topic']} (โดย {t['PIC']})", expanded=True):
                    st.write(f"**กลุ่มที่จะโพสต์:** {t['FB_Group']}")
                    # หัวหน้าแก้ไขข้อความได้โดยตรง
                    t['Draft'] = st.text_area("ข้อความที่ร่างมา (หัวหน้าแก้ไขได้ที่นี่):", value=t['Draft'], key=f"rev_{t['id']}")
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Approve", key=f"app_{t['id']}"):
                        t['Status'] = "Approved"
                        st.rerun()
                    if col2.button("❌ Reject (ตีกลับไปแก้)", key=f"rej_{t['id']}"):
                        t['Status'] = "Pending" # ส่งกลับไปสถานะแรก
                        st.rerun()

    # --- 6. FLOW: ADMIN (รับงาน & ส่งตรวจ & รายงานตัวเลข) ---
    else:
        menu = st.sidebar.radio("เมนูแอดมิน:", ["งานที่ได้รับมอบหมาย", "ส่งยอดประจำวัน"])
        
        if menu == "งานที่ได้รับมอบหมาย":
            st.title("📥 My Tasks")
            # เห็นเฉพาะงานที่ได้รับมอบหมาย
            my_tasks = [t for t in st.session_state.db if t['PIC'] == st.session_state.username]
            for t in my_tasks:
                status_color = "orange" if t['Status'] == "Pending" else "cyan" if t['Status'] == "Reviewing" else "green"
                with st.expander(f"📌 {t['Topic']} | สถานะ: {t['Status']}", expanded=True):
                    st.write(f"**Guideline:** {t['Guide']}")
                    
                    if t['Status'] == "Pending":
                        if st.button("✨ Draft with AI", key=f"ai_{t['id']}"):
                            res = call_seeding_agent(t['Topic'], t['Guide'])
                            if res: st.session_state[f"res_{t['id']}"] = res
                        
                        if f"res_{t['id']}" in st.session_state:
                            for i, m in enumerate(st.session_state[f"res_{t['id']}"]):
                                if st.button(f"เลือกแบบที่ {i+1}", key=f"s_{t['id']}_{i}"):
                                    t['Draft'] = m
                                    st.rerun()
                        
                        t['FB_Group'] = st.text_input("ใส่ชื่อ Facebook Group ที่จะโพสต์:", value=t['FB_Group'], key=f"grp_{t['id']}")
                        t['Draft'] = st.text_area("ข้อความที่จะส่งตรวจ:", value=t['Draft'], key=f"ed_{t['id']}")
                        
                        if st.button("ส่งให้หัวหน้าตรวจ (Submit for Review)", key=f"sub_{t['id']}", disabled=not (t['Draft'] and t['FB_Group'])):
                            t['Status'] = "Reviewing"
                            st.rerun()
                    
                    elif t['Status'] == "Approved":
                        st.success("✅ หัวหน้าอนุมัติแล้ว! นำข้อความด้านล่างไปโพสต์ได้เลย")
                        st.code(t['Draft']) # ง่ายต่อการก๊อปปี้

        elif menu == "ส่งยอดประจำวัน":
            st.title("📊 Daily Statistics Report")
            for t in [x for x in st.session_state.db if x['PIC'] == st.session_state.username and x['Status'] == "Approved"]:
                with st.container(border=True):
                    st.write(f"**งาน:** {t['Topic']} | **กลุ่ม:** {t['FB_Group']}")
                    c1, c2 = st.columns(2)
                    t['Post_Count'] = c1.number_input("จำนวนโพสต์", value=t['Post_Count'], key=f"pc_{t['id']}")
                    t['Comment_Count'] = c2.number_input("จำนวนคอมเมนต์", value=t['Comment_Count'], key=f"cc_{t['id']}")

    # --- 7. Daily Report (สำหรับทุกคนดูภาพรวม) ---
    if st.session_state.user_role == "Boss" and menu == "สรุปรายงานประจำวัน":
        st.title("📋 สรุปยอดรวม Seeding")
        df = pd.DataFrame(st.session_state.db)
        if not df.empty:
            st.dataframe(df[['PIC', 'Topic', 'FB_Group', 'Status', 'Post_Count', 'Comment_Count']])
            st.metric("Total Posts", df['Post_Count'].sum())
            st.metric("Total Comments", df['Comment_Count'].sum())

    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.rerun()
