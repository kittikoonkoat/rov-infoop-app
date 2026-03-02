# ส่วนที่ปรับปรุง: ฟังก์ชันบันทึกข้อมูลแบบระบุแถว (เพื่อความเร็วและลด error)
def update_task_status(task_id, updated_data):
    sh = init_connection()
    if sh:
        ws = sh.worksheet("tasks")
        # ค้นหาแถวที่มี ID ตรงกัน (ID อยู่คอลัมน์ A)
        try:
            cell = ws.find(str(task_id))
            row_idx = cell.row
            # อัปเดตข้อมูลตามลำดับคอลัมน์ (ID, Topic, PIC, Status, Guide, Persona, Draft, Date)
            # ตัวอย่างนี้เป็นการอัปเดตทั้งแถวที่เจอ
            headers = ["id", "Topic", "PIC", "Status", "Guide", "Persona", "Draft", "Date"]
            row_values = [updated_data.get(h, "") for h in headers]
            ws.update(f"A{row_idx}:H{row_idx}", [row_values])
        except Exception as e:
            st.error(f"Update Failed: {e}")

# ส่วนที่ปรับปรุง: AI Response Parsing ให้ยืดหยุ่นขึ้น
def call_ai_agent(topic, guide, persona):
    # ... (header/payload เหมือนเดิม) ...
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        res = response.json()
        
        # ดึง Text ออกมาอย่างปลอดภัย
        raw_text = res.get('data', {}).get('outputs', {}).get('text', "")
        
        # แยกข้อความโดยมองหาตัวเลขนำหน้า เช่น 1. 2. หรือขึ้นบรรทัดใหม่
        options = re.split(r'\n\d+\.|\n-', "\n" + str(raw_text))
        options = [opt.strip() for opt in options if len(opt.strip()) > 5]
        
        return options[:10]
    except Exception as e:
        return [f"❌ AI Error: {str(e)}"]
