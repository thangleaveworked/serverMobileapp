import os
from google.cloud import vision
import io

# Đặt biến môi trường cho file credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "metal-circle-429603-g4-95549c44d80c.json"

# Khởi tạo client
client = vision.ImageAnnotatorClient()

# Đường dẫn tới file ảnh cần nhận diện
image_path = "z5638442087566_98e36f8278b5336be13c7b565431a776.jpg"

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
