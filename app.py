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
