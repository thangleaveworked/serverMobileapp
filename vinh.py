import os
from google.cloud import vision
import io

# Đặt biến môi trường cho file credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:\THUCTAP\\virtual-aileron-425501-m5-c0c8cb19b03d.json"

# Khởi tạo client
client = vision.ImageAnnotatorClient()

# Đường dẫn tới file ảnh cần nhận diện
image_path = "D:\THUCTAP\images\\10.png"

# Đọc ảnh từ file
with open(image_path, "rb") as image_file:
    content = image_file.read()

image = vision.Image(content=content)

# Thực hiện nhận diện văn bản
response = client.text_detection(image=image)
texts = response.text_annotations

# In kết quả
if texts:
    print(f"Văn bản được nhận diện:\n{texts[0].description}")
else:
    print("Không tìm thấy văn bản trong ảnh.")

# Xử lý lỗi nếu có
if response.error.message:
    raise Exception(
        f"Lỗi khi nhận diện văn bản trong ảnh: {response.error.message}"
    )