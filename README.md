# 🔍 AI Expired Date Detection and Notification

> ระบบตรวจจับวันหมดอายุสินค้าอัตโนมัติด้วย AI พร้อมแจ้งเตือนผ่าน Discord

An AI-powered system that detects expiry dates on product packaging using **YOLOv8** object detection and **EasyOCR** text recognition, then sends real-time alerts to a **Discord** channel via webhook.

---

## ✨ Features

- 🎯 **Object Detection** — Uses a custom-trained YOLOv8 model to locate expiry date regions on product images
- 🔤 **OCR Text Extraction** — Reads detected regions with EasyOCR to extract date strings
- 📅 **Smart Date Parsing** — Validates and selects the most relevant expiry date from multiple candidates (supports `DDMMYYYY` and `DDMMYY` formats)
- 🚨 **Discord Notifications** — Sends color-coded embed alerts:
  - 🟢 **Green** — Product is still safe (> 3 days until expiry)
  - 🟠 **Orange** — Product is expiring soon (≤ 3 days)
  - 🔴 **Red** — Product has already expired
- ⏰ **Scheduled Auto-Processing** — Automatically scans all products at a configurable daily time
- 📸 **Image Archiving** — Saves annotated detection results to `Saved_Photo/`

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [YOLOv8](https://github.com/ultralytics/ultralytics) (Ultralytics) | Object detection model for locating expiry date regions |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | Optical Character Recognition for reading text |
| [OpenCV](https://opencv.org/) | Image processing and annotation |
| [Pandas](https://pandas.pydata.org/) | Data handling |
| [Schedule](https://schedule.readthedocs.io/) | Task scheduling for automated processing |
| [Discord Webhooks](https://discord.com/developers/docs/resources/webhook) | Real-time notification delivery |
| Python 3.x | Core programming language |

---

## 📁 Project Structure

```
Mini-Project-AI_Expire-detect/
├── main_function.py          # Main application — detection, OCR, alerts, scheduling
├── train_yolo.py             # YOLOv8 training script
├── saveconfig.txt            # Saved configuration (model path, webhook URL)
├── yolov8n.pt                # Pre-trained YOLOv8 nano base model
│
├── dataset/                  # Training dataset
│   ├── data.yaml             # YOLO dataset config (1 class: expiry_date)
│   ├── images/
│   │   ├── train/            # Training images
│   │   └── val/              # Validation images
│   └── labels/               # YOLO annotation labels
│
├── runs/                     # YOLOv8 training outputs
│   └── detect/
│       └── train10/weights/  # Best trained model weights
│
├── Product_Collect/          # Input — product images to be processed
│
├── Saved_Photo/              # Output — annotated detection results
│   └── expiry_results.csv    # Historical detection log
│
└── venv/                     # Python virtual environment
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/AI-Expired-Date-Detection-and-Notification.git
cd AI-Expired-Date-Detection-and-Notification/Mini-Project-AI_Expire-detect
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install ultralytics easyocr opencv-python pandas requests schedule
```

### 4. Configure Discord Webhook

Open `main_function.py` and replace the `DISCORD_WEBHOOK_URL` value with your own Discord webhook URL:

```python
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"
```

> 💡 **How to create a Discord Webhook:** Go to your Discord server → Channel Settings → Integrations → Webhooks → New Webhook → Copy URL

---

## 🚀 Usage

Run the main application:

```bash
python main_function.py
```

You will be prompted with two modes:

### Mode 1 — Add and Process a Single Image

```
กรุณาเลือกโหมด (1 หรือ 2): 1
กรุณาใส่ path ของรูปภาพ: path/to/your/image.jpg
กรุณาใส่ชื่อสินค้า: Product_Name
```

- The image is copied to `Product_Collect/`
- The system detects the expiry date region, reads the text via OCR, and sends a Discord alert

### Mode 2 — Batch Process All Images + Auto-Schedule

```
กรุณาเลือกโหมด (1 หรือ 2): 2
```

- Processes **all images** in the `Product_Collect/` folder
- Then starts a **daily scheduler** that repeats at the configured time

#### Change the Schedule Time

Edit the `SCHEDULE_TIME` variable in `main_function.py`:

```python
SCHEDULE_TIME = "08:00"  # Set your preferred daily check time (24-hour format)
```

---

## 🧠 How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Input Image │────▶│  YOLOv8 Detect   │────▶│  Crop ROI    │
└──────────────┘     │  (expiry_date)   │     └──────┬───────┘
                     └──────────────────┘            │
                                                     ▼
                     ┌──────────────────┐     ┌──────────────┐
                     │  Parse & Validate│◀────│  EasyOCR     │
                     │  Date Candidates │     │  Read Text   │
                     └────────┬─────────┘     └──────────────┘
                              │
                              ▼
                     ┌──────────────────┐     ┌──────────────┐
                     │  Calculate Days  │────▶│  Discord     │
                     │  Until Expiry    │     │  Webhook     │
                     └──────────────────┘     └──────────────┘
```

1. **Detection** — YOLOv8 scans the product image and identifies bounding boxes around expiry date regions
2. **OCR** — EasyOCR extracts text from each detected region
3. **Parsing** — Regex extracts numeric date candidates (`DDMMYYYY` or `DDMMYY`); the system validates them and selects the best match
4. **Classification** — Compares the detected date against today's date to determine status (expired / expiring soon / safe)
5. **Notification** — Sends a rich embed message to Discord with product name, expiry date, days remaining, and detection confidence
6. **Archiving** — Saves the annotated cropped image to `Saved_Photo/`

---

## 🏋️ Training Your Own Model

If you want to retrain the YOLOv8 model with your own dataset:

1. **Prepare your dataset** in YOLO format under `dataset/`:
   - Place training images in `dataset/images/train/`
   - Place validation images in `dataset/images/val/`
   - Place corresponding label `.txt` files in `dataset/labels/train/` and `dataset/labels/val/`

2. **Update `dataset/data.yaml`**:
   ```yaml
   train: dataset/images/train
   val: dataset/images/val

   nc: 1
   names: ['expiry_date']
   ```

3. **Run the training script**:
   ```bash
   python train_yolo.py
   ```
   The model trains for **200 epochs** at image size **640×640** with batch size **8** using YOLOv8n as the base.

4. **Update the model path** in `main_function.py` to point to your new best weights:
   ```python
   model = YOLO("runs/detect/trainX/weights/best.pt")
   ```

---

## 📨 Discord Alert Examples

| Status | Color | Message |
|---|---|---|
| ✅ Safe | 🟢 Green | Product will expire in **X** days |
| ⚠️ Expiring Soon | 🟠 Orange | Product will expire within **≤ 3** days |
| ❌ Expired | 🔴 Red | Product has already expired |

Each alert includes:
- Product name
- Expiry date
- Detection confidence score
- Timestamp of when the scan was performed

---

## 📋 Requirements

- Python 3.8+
- Webcam or product images
- Discord server with webhook access
- GPU recommended (but CPU is supported via `gpu=False` in EasyOCR config)

---

## 📝 License

This project is for educational purposes as part of an AI mini-project.

---

## 👥 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.
