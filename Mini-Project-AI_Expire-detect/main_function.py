import cv2
from ultralytics import YOLO
import easyocr
import re
import os
from datetime import datetime
import pandas as pd
import requests
import schedule
import time

# ========================== ตั้งค่า ==========================
model = YOLO("runs/detect/train10/weights/best.pt")
reader = easyocr.Reader(['en'], gpu=False)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1425512759734571031/KWjq40nV8pSyx1qNk4ZWMIAi7HQ8je0V9-JKXOQ7zeCnro3uKt5VbymGtTd8o2AOscBQ"

# 🕒 ตั้งเวลาอัตโนมัติ (แก้เวลาที่นี่ได้เลย)
SCHEDULE_TIME = "18:04"  # เช่น "08:00", "12:30", "23:00"

# ========================== ฟังก์ชันแจ้งเตือน Discord ==========================
def send_discord_alert_embed(product_name, expiry_date, days_left, confidence, saved_time):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ ยังไม่ได้ตั้งค่า DISCORD_WEBHOOK_URL")
        return

    if days_left < 0:
        color = 0xFF0000
        title = "❌ หมดอายุแล้ว"
        message = f"**{product_name}** หมดอายุเมื่อ `{expiry_date}`"
    elif 0 <= days_left <= 3:
        color = 0xFFA500
        title = "⚠️ ใกล้หมดอายุ"
        message = f"**{product_name}** จะหมดอายุในอีก `{days_left}` วัน (`{expiry_date}`)"
    else:
        color = 0x00FF00
        title = "✅ ยังไม่หมดอายุ"
        message = f"**{product_name}** จะหมดอายุภายใน `{days_left}` วัน (`{expiry_date}`)"

    embed = {
        "title": title,
        "description": message,
        "color": color,
        "fields": [
            {"name": "Confidence", "value": f"{confidence:.2f}", "inline": True},
            {"name": "บันทึกเมื่อ", "value": saved_time, "inline": True},
        ],
        "footer": {"text": "🔍 Expiry Date Detection System"}
    }

    data = {"embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code not in [200, 204]:
            print(f"⚠️ ส่งข้อความ Discord ไม่สำเร็จ ({response.status_code})")
        else:
            print("📨 ส่งแจ้งเตือนเข้า Discord สำเร็จ!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการส่ง Discord: {e}")

# ========================== ฟังก์ชัน OCR และประมวลผลวันหมดอายุ ==========================
def extract_expiry_candidates(text):
    text_clean = text.replace(" ", "").replace("-", "").replace(".", "")
    return re.findall(r'\d{6,8}', text_clean)

def validate_and_select_expiry(candidates, current_year=None, only_future=None):
    if current_year is None:
        current_year = datetime.now().year
    valid_dates = []
    for c in candidates:
        try:
            if len(c) == 8:
                day = int(c[:2])
                month = int(c[2:4])
                year = int(c[4:8])
            elif len(c) == 6:
                day = int(c[:2])
                month = int(c[2:4])
                year = int(c[4:6]) + 2000
            else:
                continue
            if only_future is True and year >= current_year:
                valid_dates.append(f"{c[:2]}{c[2:4]}{year:04d}")
            elif only_future is False and year < current_year:
                valid_dates.append(f"{c[:2]}{c[2:4]}{year:04d}")
            elif only_future is None:
                valid_dates.append(f"{c[:2]}{c[2:4]}{year:04d}")
        except ValueError:
            continue
    if not valid_dates:
        return ''
    return max(valid_dates, key=lambda x: int(x[4:8]))

# ========================== ฟังก์ชันหลักประมวลผลภาพ ==========================
def process_image(image_path, product_name):
    output_folder = 'Saved_Photo'
    os.makedirs(output_folder, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ โหลดรูปไม่สำเร็จ: {image_path}")
        return

    results = model(img)
    expiry_candidates = []
    block_images = []

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped_img = img[y1:y2, x1:x2]
            if cropped_img.size == 0:
                continue

            cls = int(box.cls[0])
            conf = float(box.conf[0])
            ocr_results = reader.readtext(cropped_img)
            candidates = []
            for (_, text, _) in ocr_results:
                candidates += extract_expiry_candidates(text)

            if candidates:
                expiry_candidates.extend(candidates)
                block_images.append({
                    'img': cropped_img,
                    'cls': cls,
                    'conf': conf,
                    'candidates': candidates
                })

    if not block_images:
        print("📁 ไม่พบวัตถุที่ตรวจจับได้")
        return

    today = datetime.now()
    current_time = today.strftime("%Y-%m-%d %H:%M:%S")
    current_year = today.year
    real_expiry = validate_and_select_expiry(expiry_candidates, current_year=current_year, only_future=True)

    # ------------------ กรณีไม่พบวันหมดอายุในอนาคต ------------------
    if not real_expiry:
        print("⚠️ ไม่พบวันหมดอายุในอนาคต — ตรวจสอบ candidate หมดอายุแล้ว")
        all_expired = []
        for block in block_images:
            for c in block['candidates']:
                try:
                    if len(c) == 8:
                        day = int(c[:2]); month = int(c[2:4]); year = int(c[4:8])
                    elif len(c) == 6:
                        day = int(c[:2]); month = int(c[2:4]); year = int(c[4:6]) + 2000
                    else:
                        continue
                    if year < current_year:
                        all_expired.append({
                            "date": f"{day:02d}{month:02d}{year:04d}",
                            "year": year,
                            "img": block['img'],
                            "conf": block['conf']
                        })
                except ValueError:
                    continue

        if not all_expired:
            print("📁 ไม่พบวันหมดอายุที่ตรวจสอบได้ในภาพนี้")
            return

        latest_expired = max(all_expired, key=lambda x: int(x["date"][4:8]+x["date"][:4]+x["date"][2:4]))
        best_img = latest_expired["img"].copy()
        latest_date = latest_expired["date"]
        best_img_conf = latest_expired["conf"]

        cv2.putText(best_img, "EXPIRED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        filename = f"{output_folder}/expired_{product_name}_{latest_date}.jpg"
        cv2.imwrite(filename, best_img)
        formatted_expiry = f"{latest_date[:2]}/{latest_date[2:4]}/{latest_date[4:8]}"
        send_discord_alert_embed(product_name, formatted_expiry, -1, best_img_conf, current_time)
        return

    # ------------------ กรณีพบวันหมดอายุในอนาคต ------------------
    # ใช้ block_images[0] หรือเลือก block ที่มี confidence สูงสุด
    best_block = max(block_images, key=lambda b: b['conf'])
    best_img = best_block['img'].copy()
    best_conf = best_block['conf']

    formatted_expiry = f"{real_expiry[:2]}/{real_expiry[2:4]}/{real_expiry[4:8]}"
    expiry_date_obj = datetime.strptime(formatted_expiry, "%d/%m/%Y")
    days_left = (expiry_date_obj - today).days

    color = (0, 255, 0) if days_left > 3 else (0, 165, 255) if 0 <= days_left <= 3 else (0, 0, 255)
    cv2.putText(best_img, formatted_expiry, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    filename = f"{output_folder}/{product_name}_{formatted_expiry.replace('/', '')}.jpg"
    cv2.imwrite(filename, best_img)

    print(f"📌 ตรวจพบวันหมดอายุ: {formatted_expiry}")
    send_discord_alert_embed(product_name, formatted_expiry, days_left, best_conf, current_time)

# ========================== โหมด 2: ประมวลผลภาพทั้งหมด ==========================
def process_all_images_in_collect():
    product_folder = 'Product_Collect'
    os.makedirs(product_folder, exist_ok=True)
    images = [f for f in os.listdir(product_folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    if not images:
        print("⚠️ ไม่มีภาพในโฟลเดอร์ Product_Collect")
        return

    print(f"🧩 พบ {len(images)} ภาพใน Product_Collect — เริ่มประมวลผล...")
    for img_file in images:
        product_name = os.path.splitext(img_file)[0]
        image_path = os.path.join(product_folder, img_file)
        process_image(image_path, product_name)
    print("✅ ประมวลผลภาพทั้งหมดเสร็จสิ้น")

# ========================== ตั้งเวลาอัตโนมัติ ==========================
def start_auto_processing():
    print(f"⏰ ตั้งเวลาประมวลผลอัตโนมัติทุกวันเวลา {SCHEDULE_TIME}")
    schedule.every().day.at(SCHEDULE_TIME).do(process_all_images_in_collect)
    while True:
        schedule.run_pending()
        time.sleep(30)

# ========================== เมนูหลัก ==========================
print("=== ระบบตรวจวันหมดอายุสินค้า ===")
print("1️⃣ เพิ่มรูปใหม่")
print("2️⃣ ประมวลผลภาพทั้งหมดใน Product_Collect (และตั้งเวลาทำงานอัตโนมัติ)")
mode = input("กรุณาเลือกโหมด (1 หรือ 2): ").strip()

if mode == "1":
    image_path = input("กรุณาใส่ path ของรูปภาพ: ").strip()
    if not os.path.exists(image_path):
        print(f"❌ ไม่พบไฟล์รูป: {image_path}")
        exit()
    product_name = input("กรุณาใส่ชื่อสินค้า: ").strip().replace(" ", "_")

    os.makedirs("Product_Collect", exist_ok=True)
    new_path = os.path.join("Product_Collect", f"{product_name}.jpg")
    cv2.imwrite(new_path, cv2.imread(image_path))
    print(f"📁 บันทึกภาพต้นฉบับไว้ใน Product_Collect: {new_path}")
    process_image(new_path, product_name)

elif mode == "2":
    process_all_images_in_collect()
    start_auto_processing()
else:
    print("❌ ตัวเลือกไม่ถูกต้อง กรุณาเลือก 1 หรือ 2")
