import google.generativeai as genai
import easyocr
import numpy as np
from PIL import Image

# Cấu hình API key cho GenAI
API_KEY = "AIzaSyBbUxzdsTigSAcuCcQ4wFMUyq_PayWmU5E"  # Thay YOUR_API_KEY bằng API key của bạn
genai.configure(api_key=API_KEY)

def extract_text_from_image(image_path):
    # Tạo đối tượng reader của EasyOCR
    reader = easyocr.Reader(['vi', 'en'], gpu=True)

    # Đọc hình ảnh
    image = Image.open(image_path)

    # Tăng độ phân giải của ảnh
    width, height = image.size
    new_width = width * 5
    new_height = height * 5
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    # Chuyển đổi ảnh nhị phân thành mảng numpy
    binary_image_array = np.array(resized_image)

    # Đọc văn bản từ hình ảnh nhị phân
    result = reader.readtext(binary_image_array)

    # Ghép các đoạn văn bản thành một chuỗi duy nhất
    extracted_text = '\n'.join([text[1] for text in result])

    return extracted_text

def interact_with_gemini(prompt, history=[]):
    # Tạo đối tượng mô hình GenerativeAI
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    chat = model.start_chat(history=history)

    # Gửi câu hỏi cho mô hình GenAI và nhận câu trả lời
    response = chat.send_message(prompt)

    # Trích xuất nội dung văn bản từ câu trả lời của GenAI
    text_response = response.text

    return text_response

# Sử dụng hàm extract_text_from_image để trích xuất toàn bộ văn bản từ hình ảnh
image_path = 'D:\\THUCTAP\\images\\5.png'
extracted_text = extract_text_from_image(image_path)
print(extracted_text)

# Sử dụng hàm interact_with_gemini để tương tác với mô hình GenAI
prompt = "tôi có một hóa đơn tính tiền được OCR ra nhưng bị lỗi chữ, hãy giúp tôi hoàn thành các câu và từ còn sai rồi trích xuất những thông tin trong hóa đơn nếu có: tổ chức lập hóa đơn, ngày lập hóa đơn, tên sản phẩm, số lượng mỗi sản phẩm, giá sản phẩm, tổng số tiền thanh toán: (chú ý: trả lời dúng những mục tôi yêu cầu không thêm bớt và trả về dạng JSON)"
gemini_response = interact_with_gemini(prompt+"\n"+extracted_text)
print("Gemini: " + gemini_response)
