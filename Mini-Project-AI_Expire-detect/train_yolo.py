from ultralytics import YOLO

# โหลดโมเดลเริ่มต้น (เลือกขนาดได้: n, s, m, l, x)
model = YOLO("yolov8n.pt")

# เทรน
model.train(
    data="dataset/data.yaml",
    epochs=200,
    imgsz=640,
    batch=8,
)
