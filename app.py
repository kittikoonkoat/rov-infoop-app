import streamlit as st
import pandas as pd
from datetime import datetime

# --- การตั้งค่าเบื้องต้น ---
st.set_page_config(page_title="RoV Seeding System", layout="wide")

# --- ส่วนจัดการข้อมูล (จำลองฐานข้อมูล) ---
if 'db' not in st.session_state:
    st.session_state.db = []

# --- ฟังก์ชันช่วยเหลือ ---
def add_task(topic, guide, pic, target, publish_time):
    new_task = {
        "id": len(st.session_state.db) + 1,
        "Topic": topic,
        "Message Guide": guide,
        "Message PIC": pic,
        "Target Channel": target,
        "Draft Message": "",
        "Status": "Waiting for Draft", # สถานะ: รอ PIC ร่างข้อความ
        "Publish Time": publish_time,
        "Link Post": "",
        "Likes": 0,
        "Comments": 0
    }
    st.session_state.db.append(new_task)

# --- ส่วนของเมนูหลัก ---
menu = st.sidebar.selectbox("เลือกหน้าการใช้งาน", ["Admin (วางแผน/ตรวจงาน)", "PIC (พื้นที่คนทำงาน/25 Accounts)", "Daily Report (สรุปผล)"])

# ---------------------------------------------------------
# หน้าที่ 1: ADMIN - สำหรับหัวหน้างาน
# ---------------------------------------------------------
if menu == "Admin (วางแผน/ตรวจงาน)":
    st.title("👨‍💼 Admin Control Panel")
    
    with st.expander("➕ เพิ่มงานใหม่ (Add New Topic)"):
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            topic = col1.text_input("Topic (หัวข้อ)")
            pic = col2.selectbox("มอบหมายให้ PIC", ["PIC_A (ดูแล Acc 1-25)", "PIC_B (ดูแล Acc 26-50)"])
            guide = st.text_area("Message Guide (แนวทางข้อความ)")
            target = st.text_input("Target Channel (ลิงก์กลุ่ม/เพจ)")
            p_time = st.text_input("Publish Time (เวลาที่ควรโพสต์)", value="18:00")
            
            if st.form_submit_button("เพิ่มงานเข้าระบบ"):
                add_task(topic, guide, pic, target, p_time)
                st.success("เพิ่มงานเรียบร้อย!")

    st.subheader("📋 รายงานสถานะงานทั้งหมด")
    if st.session_state.db:
        df = pd.DataFrame(st.session_state.db)
        st.dataframe(df[['id', 'Topic', 'Message PIC', 'Status', 'Publish Time']])
        
        # ระบบอนุมัติงาน
        st.divider()
        st.subheader("✅ ตรวจสอบและอนุมัติ Draft")
        pending_tasks = [t for t in st.session_state.db if t['Status'] == "Pending Approval"]
        if pending_tasks:
            for t in pending_tasks:
                with st.container(border=True):
                    st.write(f"**จาก:** {t['Message PIC']} | **หัวข้อ:** {t['Topic']}")
                    st.info(f"**ข้อความที่ร่างมา:** {t['Draft Message']}")
                    col_a, col_b = st.columns(2)
                    if col_a.button(f"อนุมัติ #{t['id']}", key=f"app_{t['id']}"):
                        t['Status'] = "Approved (Ready to Post)"
                        st.rerun()
                    if col_b.button(f"ส่งกลับไปแก้ #{t['id']}", key=f"rej_{t['id']}"):
                        t['Status'] = "Need Revision"
                        st.rerun()
        else:
            st.write("ยังไม่มี Draft ส่งเข้ามาตรวจ")

# ---------------------------------------------------------
# หน้าที่ 2: PIC - สำหรับคนดูแล 25 แอคเคาท์
# ---------------------------------------------------------
elif menu == "PIC (พื้นที่คนทำงาน/25 Accounts)":
    st.title("🎮 PIC Workspace")
    
    # ส่วนจัดการ 25 Accounts
    with st.sidebar:
        st.subheader("My 25 Accounts")
        acc_list = [f"RoV_User_{i:02d}" for i in range(1, 26)]
        selected_acc = st.selectbox("เลือกบัญชีที่จะใช้โพสต์:", acc_list)
        st.success(f"กำลังใช้งาน: {selected_acc}")

    # แสดงงานที่ได้รับมอบหมาย
    my_tasks = [t for t in st.session_state.db if t['Status'] in ["Waiting for Draft", "Need Revision", "Approved (Ready to Post)"]]
    
    if not my_tasks:
        st.info("วันนี้ยังไม่มีงานที่ได้รับมอบหมาย")
    else:
        for t in my_tasks:
            with st.expander(f"📌 งาน: {t['Topic']} (สถานะ: {t['Status']})"):
                st.write(f"**Guide:** {t['Message Guide']}")
                st.write(f"**เป้าหมาย:** {t['Target Channel']}")
                
                # AI Helper
                if st.button(f"✨ ใช้ AI ช่วยเกลาข้อความ #{t['id']}"):
                    st.write("---")
                    st.write("**AI Suggested (เนียนแบบผู้เล่นจริง):**")
                    st.code(f"เอาจริงแพตช์นี้ {t['Topic']} มันก็ไม่ได้แย่นะ ลองเล่นแล้วฟีลลิ่งโคตรได้ ใครยังไม่ลองไปลองดู")
                
                # ช่องร่างข้อความ
                draft = st.text_area("ร่างข้อความของคุณที่นี่:", value=t['Draft Message'], key=f"txt_{t['id']}")
                
                col1, col2 = st.columns(2)
                if col1.button("ส่งให้หัวหน้าตรวจ", key=f"send_{t['id']}"):
                    t['Draft Message'] = draft
                    t['Status'] = "Pending Approval"
                    st.rerun()
                
                # ปุ่มไปโพสต์จริง (เฉพาะที่อนุมัติแล้ว)
                if t['Status'] == "Approved (Ready to Post)":
                    st.success("งานนี้ผ่านการอนุมัติแล้ว! กดคัดลอกและไปโพสต์ได้เลย")
                    st.markdown(f'<a href="{t["Target Channel"]}" target="_blank">🔗 เปิด Facebook Group</a>', unsafe_allow_html=True)
                    
                    # บันทึกหลังโพสต์
                    st.divider()
                    l_post = st.text_input("วางลิงก์ที่โพสต์แล้ว:", key=f"link_{t['id']}")
                    if st.button("บันทึกการโพสต์สำเร็จ", key=f"done_{t['id']}"):
                        t['Link Post'] = l_post
                        t['Status'] = "Published"
                        st.balloons()
                        st.rerun()

# ---------------------------------------------------------
# หน้าที่ 3: DAILY REPORT
# ---------------------------------------------------------
else:
    st.title("📊 Daily Summary Report")
    if st.session_state.db:
        df_all = pd.DataFrame(st.session_state.db)
        
        # สรุปตัวเลข
        c1, c2, c3 = st.columns(3)
        c1.metric("งานทั้งหมด", len(df_all))
        c2.metric("โพสต์สำเร็จแล้ว", len(df_all[df_all['Status']=="Published"]))
        c3.metric("ยอด Like รวม", df_all['Likes'].sum())
        
        st.subheader("ตารางสรุปผลงานวันนี้")
        st.dataframe(df_all[['Topic', 'Message PIC', 'Status', 'Link Post']])
    else:
        st.write("ยังไม่มีข้อมูลของวันนี้")
