import os
from google.cloud import vision
import io
import requests

def detect_text_in_image(image_content):
    # Đặt biến môi trường cho file credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "metal-circle-429603-g4-95549c44d80c.json"

    # Khởi tạo client
    client = vision.ImageAnnotatorClient()

    # Chuyển đổi nội dung ảnh thành định dạng mà Vision API hiểu
    image = vision.Image(content=image_content)

    # Thực hiện nhận diện văn bản
    response = client.text_detection(image=image)
    texts = response.text_annotations

    # Kiểm tra và trả về kết quả
    if texts:
        return texts[0].description
    else:
        return "Không tìm thấy văn bản trong ảnh."

    # Xử lý lỗi nếu có
    if response.error.message:
        raise Exception(
            f"Lỗi khi nhận diện văn bản trong ảnh: {response.error.message}"
        )

# URL của ảnh cần nhận diện
# image_url = "https://firebasestorage.googleapis.com/v0/b/thuctap-f37c9.appspot.com/o/images%2F1721120999290_468?alt=media&token=5f7bce65-820a-4dfd-a547-330843c8a16a"
# recognized_text = detect_text_in_image(image_url)
# print(recognized_text)
