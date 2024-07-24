import google.generativeai as genai

API_KEY = "AIzaSyBbUxzdsTigSAcuCcQ4wFMUyq_PayWmU5E"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

while True:
    text='''
'''
    a=input("Enter: ")
    user_input = "tôi có một hóa đơn tính tính tiền được OCR ra nhưng bị lỗi chữ, giúp tôi lấy những thông tin trong hóa nếu có: tên khách hàng, tổng số tiền thanh toán: (chú ý: trả lời dúng những mục tôi yêu cầu không thêm bớt và tra vè dang json) "
    response = chat.send_message(user_input + text)
    # Trích xuất nội dung văn bản từ response
    text_response = response.text  # Sửa đổi nếu thuộc tính chứa nội dung khác
    print("Gemini: " + text_response)