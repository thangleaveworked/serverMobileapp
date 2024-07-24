from flask import Flask, request, jsonify
import requests
import os
from io import BytesIO
import google.generativeai as genai
import easyocr
import numpy as np
from PIL import Image
import json
import mysql.connector
from datetime import datetime
from send_email import send_email
import random
from vision_API import detect_text_in_image
import re

# Cấu hình API key cho GenAI
API_KEY = "AIzaSyBbUxzdsTigSAcuCcQ4wFMUyq_PayWmU5E"  # Thay YOUR_API_KEY bằng API key của bạn
genai.configure(api_key=API_KEY)

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'thuctap'
}
def extract_text_from_image(image):
    # Tạo đối tượng reader của EasyOCR
    reader = easyocr.Reader(['vi', 'en'], gpu=True)

    # Tăng độ phân giải của ảnh
    width, height = image.size
    new_width = width * 5
    new_height = height * 5
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    # Chuyển đổi ảnh nhị phân thành mảng numpy
    binary_image_array = np.array(resized_image)

    # Đọc văn bản từ hình ảnh nhị phân
    result = reader.readtext(binary_image_array)
    print(result)
    # Ghép các đoạn văn bản thành một chuỗi duy nhất
    extracted_text = '\n'.join([text[1] for text in result])

    ocr_data = {text[1]: text[2] for text in result}
    print(extracted_text)
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

# Hàm tải ảnh từ URL và lưu vào file cục bộ
# def download_image_from_url(url):
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             image = Image.open(BytesIO(response.content))
#             print(f"Đã tải ảnh thành công từ: {url}")
#             return image
#         else:
#             print(f"Lỗi khi tải ảnh từ URL, mã lỗi: {response.status_code}")
#             return None
#     except Exception as e:
#         print(f"Lỗi khi tải ảnh từ URL: {e}")
#         return None
def download_image_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            print(f"Đã tải ảnh thành công từ: {url}")
            return response.content  # Trả về nội dung ảnh
        else:
            print(f"Lỗi khi tải ảnh từ URL, mã lỗi: {response.status_code}")
            return None
    except Exception as e:
        print(f"Lỗi khi tải ảnh từ URL: {e}")
        return None

def convert_json_to_text(json_data):
    output = []
    response = json_data

    output.append(f"Tên cửa hàng: {response.get('ten cua hang', '0')}")
    output.append(f"Thời gian: {response.get('thoi gian', '0')}")
    output.append("Sản phẩm thu:")

    for product in response["san pham"]:
        ten_san_pham = product.get('ten san pham', '0')
        so_luong = product.get('so luong', '0') if product.get('so luong') is not None else '0'
        don_gia = product.get('don gia', '0') if product.get('don gia') is not None else '0'
        giam_gia = product.get('giam gia', '0') if product.get('giam gia') is not None else '0'

        output.append(f"    Tên sản phẩm: {ten_san_pham}")
        output.append(f"    Số lượng sản phẩm: {so_luong}")
        output.append(f"    Đơn giá: {don_gia}")
        output.append(f"    Giảm giá: {giam_gia}")

    tien_thue_GTGT = response.get('tien thue GTGT', '0') if response.get('tien thue GTGT') is not None else '0'
    # tong_tien_thanh_toan = response.get('tong tien thanh toan', '0') if response.get('tong tien thanh toan') is not None else '0'
    # khoan thue khac
    khoanthuekhac = response.get('khoan thue khac', '0') if response.get('khoan thue khac') is not None else '0'
    output.append(f"Tiền thuế khác: {khoanthuekhac}")
    output.append(f"Tiền thuế GTGT: {tien_thue_GTGT}")
    # output.append(f"Tổng tiền thanh toán: {tong_tien_thanh_toan}")

    result = "\n".join(output)
    return result


def convert_to_json(response_text):
    # Loại bỏ các ký tự không cần thiết và chuyển đổi thành đối tượng JSON
    try:
        # Tìm phần JSON trong chuỗi
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == -1:
            raise ValueError("Không tìm thấy JSON trong chuỗi")

        json_str = response_text[json_start:json_end]

        # Chuyển đổi chuỗi JSON thành đối tượng Python
        json_data = json.loads(json_str)
        return json_data
    except Exception as e:
        print(f"Lỗi khi chuyển đổi sang JSON: {e}")
        return None


def get_transactions(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        select_query = """
        SELECT transaction_id, transaction_amount, category_id, date, description, transaction_type, note FROM transactions
        WHERE user_id = %s and status = 1
        """
        cursor.execute(select_query, (user_id,))
        transactions = cursor.fetchall()

        # Chuyển đổi dữ liệu thành định dạng JSON
        transactions_list = []
        for transaction in transactions:
            transaction_dict = {
                'transaction_id': transaction[0],
                'amount': transaction[1],
                'category_id': transaction[2],
                'date': transaction[3].strftime('%Y-%m-%d'),
                'description': transaction[4],
                'type': transaction[5],
                'note': transaction[6]
            }
            transactions_list.append(transaction_dict)

        # Chuyển danh sách thành JSON
        transactions = json.dumps(transactions_list, ensure_ascii=False)
        return transactions
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_amount(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        select_query = """select wallet from users where user_id = %s"""
        cursor.execute(select_query, (user_id,))
        wallet = cursor.fetchone()[0]

        update = """
        UPDATE users 
        SET amount = 
            (SELECT IFNULL(SUM(transaction_amount), 0) FROM transactions WHERE user_id = %s AND transaction_type = 'income') - 
            (SELECT IFNULL(SUM(transaction_amount), 0) FROM transactions WHERE user_id = %s AND transaction_type = 'expense') + %s
        WHERE user_id = %s
        """
        cursor.execute(update, (user_id, user_id, wallet, user_id))
        conn.commit()

        # Cập nhật lại và lấy ra số tiền trong bảng user
        cursor.execute("SELECT amount FROM users WHERE user_id = %s", (user_id,))
        total_amount = cursor.fetchone()[0]
        return total_amount
    except mysql.connector.Error as err:
        print(f"Error nè: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_categories(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        select_query = """
        SELECT category_id, category_name, category_icon, category_type FROM categories
        WHERE (user_id = %s OR user_id IS NULL) AND status = 1
        """
        cursor.execute(select_query, (user_id,))
        categories = cursor.fetchall()

        # Chuyển đổi dữ liệu thành định dạng JSON
        categories_list = []
        for category in categories:
            category_dict = {
                'category_id': category[0],
                'category_name': category[1],
                'category_icon': category[2],
                'category_type': category[3]
            }
            categories_list.append(category_dict)

        # Chuyển danh sách thành JSON
        categories_json = json.dumps(categories_list, ensure_ascii=False)
        return categories_json
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

# tạo đoạn đánh giá khi thêm các giao dịch mới bằng gemini
def create_notification(user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        select_wallet = """select amount from users where user_id = %s"""
        cursor.execute(select_wallet, (user_id,))
        amount = cursor.fetchone()[0]

        select_transaction = """
        select transaction_amount, date, transaction_type, note from transactions where user_id = %s
        """
        cursor.execute(select_transaction, (user_id,))
        transactions = cursor.fetchall()
        prompt1 = "số tiền trong ví của tôi là: " + str(amount) + "\nCác giao dịch mới nhất của tôi là: \n"
        data_str = ""
        for transaction in transactions:
            transaction_amount, date, transaction_type, note = transaction
            print(transaction_amount, date, transaction_type, note)
            date_str = date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(date, datetime) else date
            data_str += (
                f"{date_str};"
                f"{transaction_amount};"
                f"{transaction_type};"
                f"{note}\n"
            )
        prompt="""tôi cần bạn giúp tạo một đoạn thông báo cảnh báo ngắn để người dùng biết về tình hình tài chính của họ. Thông tin của người dùng mà tôi sẽ cung cấp bao gồm:"""
        prompt2="""Tôi muốn cảnh báo về các vấn đề sau đây:
                    Khoản chi quá lớn 
                    Số tiền còn lại trong ví quá ít
                    Thu nhập không ổn định
                    khoảng thu bất thường
                    Hãy sử dụng thông tin này để viết một đoạn text cảnh báo ngắn khoản 2 câu, dễ hiểu và thân thiện với người dùng."""
        gemini_response = interact_with_gemini(prompt +prompt1+ ":\n" + data_str + "\n" + prompt2)
        return gemini_response
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_status_transaction(transaction_id,status):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        if status == 1:
            update_query = """
            UPDATE transactions set status = 1 where transaction_id = %s"""
            cursor.execute(update_query, (transaction_id,))
            conn.commit()

        else:
            update_query = """
            UPDATE transactions set status = 0 where transaction_id = %s"""
            cursor.execute(update_query, (transaction_id,))
            conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_transaction(transaction_id, amount, date, description, note, user_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        date_obj = datetime.strptime(date, '%d/%m/%Y')
        formatted_date = date_obj.strftime('%Y-%m-%d')

        update_query = """
        UPDATE transactions 
        SET transaction_amount = %s, date = %s, description = %s, note = %s
        WHERE transaction_id = %s AND user_id = %s
        """
        cursor.execute(update_query, (amount, formatted_date, description, note, transaction_id, user_id))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        cursor.close()
        conn.close()


# # Ví dụ sử dụng hàm get_categories
# user_id = 1
# categories = get_categories(user_id)
# if categories:
#     for category in categories:
#         print(category)
# else:
#     print("No categories found or an error occurred.")


# Định nghĩa route cho endpoint "/api"
@app.route('/api', methods=['POST'])
def handle_api_request():
    request_data = request.json
    request_type = request_data.get('type')
    # print(request_type)
    if request_type == 'extract_text':
        user_id = request_data.get('user_id')
        image_url = request_data.get('image_url')
        if not image_url or not user_id:
            return jsonify({'message': 'Image URL not provided'}), 400

        image = download_image_from_url(image_url)
        if image:
            extracted_text = detect_text_in_image(image)
            print(extracted_text)
        if image is None:
            return jsonify({'message': 'Failed to download image'}), 400

        # extracted_text = extract_text_from_image(image)
        # extracted_text = detect_text_in_image(image_url)

        prompt =  """
    Tôi có đoạn text được OCR từ 1 hóa đơn thu chi hãy chuẩn hóa và hoàn thiện các câu từ trong đoạn cho đúng rồi trích xuất thông tin từ hóa đơn đó với các trường sau nếu phù hợp:

    Các trường cần lấy:
    - ten cua hang
    - thoi gian
    - san pham
        - ten san pham
        - so luong
        - giam gia
        - don gia
    - tien thue GTGT
    - khoan thue khac
    - tong tien thanh toan
    - ghi chu noi dung hoa don

    Trả về dạng JSON, các giá tiền trong hóa đơn phải là kiểu int, các key không để dấu, nếu trường tổng số tiền không có thông tin thì trả về "không đủ thông tin",ghi chú nội dung hóa đơn bằng vài từ ngắn gon, chú ý: định dạng lại thời gian dạng **/**/****, đặc biệt: chỉ trả lời chuỗi json theo yêu cầu không thêm bớt nội dung.
    """

        gemini_response = interact_with_gemini(prompt + ":\n" + extracted_text)

        print("Gemini Response:", gemini_response)

        # Chuyển đổi phản hồi JSON thành đối tượng Python
        text = convert_to_json(gemini_response)
        print("Extracted Text:", text)
        jsontext = convert_json_to_text(text)

        # total_amount = text.get('tong tien thanh toan', '0')
        # print(total_amount)
        # total_amount = str(total_amount)

        # if '.' in total_amount or ',' in total_amount:
        #     total_amount = total_amount.replace('.', '').replace(',', '')
        # print("tong tien sau khi cat"+total_amount)
        total_amount = text.get('tong tien thanh toan', '0')
        if isinstance(total_amount, str):
            total_amount = total_amount.replace('.', '').replace(',', '')
        print("tong tien sau khi cat: " + str(total_amount))
        # if total_amount.isdigit():
        #     total_amount = int(total_amount)
        # else:
        #     total_amount = 0  # Nếu không phải số, gán total_amount thành 0
        response_data = {
            'message': 'Processed the image and extracted text successfully!',
            'description': jsontext,
            'total_amount': total_amount,
            'ghichu': text.get('ghi chu noi dung hoa don', '0'),
            'date': text.get('thoi gian', '0')
        }
        return jsonify(response_data)


    elif request_type == 'update_transaction':
        user_id = request_data.get('user_id')
        transaction_id = request_data.get('transaction_id')
        amount = request_data.get('amount')
        date = request_data.get('date')
        description = request_data.get('description')
        note = request_data.get('note')

        if not user_id or not transaction_id or not amount or not date or not description or not note:
            return jsonify({'message': 'Missing required fields'}), 400

        if update_transaction(transaction_id, amount, date, description, note, user_id):
           return jsonify({'message': 'Transaction updated successfully!'})
        else:
            response_data = {
                'message': 'Failed to update transaction'
            }
        return jsonify(response_data)




    elif request_type == 'update_status_transaction':
        transaction_id = request_data.get('transaction_id')
        status = request_data.get('status')

        if not transaction_id or not status:
            return jsonify({'message': 'Missing required fields'}), 400

        if update_status_transaction(transaction_id, status):
            return jsonify({'message': 'Transaction status updated successfully!'})
        else:
            response_data = {
                'message': 'Failed to update transaction status'
            }
        return jsonify(response_data)




    elif request_type == "insert_transactions":
        user_id = request_data.get('user_id')
        amount = request_data.get('amount')
        category_id = request_data.get('category_id')
        date = request_data.get('date')
        description = request_data.get('description')

        transaction_type = request_data.get('transaction_type')
        note = request_data.get('note')


        print(user_id, amount, category_id, date, description, transaction_type, note)
        if not user_id or not amount or not category_id or not date or not transaction_type:
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            date_obj = datetime.strptime(date, '%d/%m/%Y')
            formatted_date = date_obj.strftime('%Y-%m-%d')

            insert_query = """
               INSERT INTO transactions (transaction_amount, category_id, date, description, transaction_type, user_id, note)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               """
            cursor.execute(insert_query,(amount, category_id, formatted_date, description, transaction_type, user_id, note))
            conn.commit()
            select_user = """select amount, user_email, user_name, wallet from users where user_id = %s"""
            cursor.execute(select_user, (user_id,))
            user_data = cursor.fetchone()
            total_amount = update_amount(user_id)

            transactions_list = get_transactions(user_id)
            categories_list = get_categories(user_id)
            if int(amount) < 0 or int(amount) > 1000000:
                notification = create_notification(user_id)
            else:
                notification = None


            response_data = {
                'message': 'Transaction added successfully!',
                'user_id': user_id,
                "amount": total_amount,
                "wallet": user_data[3],
                "user_email": user_data[1],
                "user_name": user_data[2],
                "transactions": transactions_list,
                "categories": categories_list,
                "notification":notification
            }
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return jsonify({'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify(response_data)




    elif request_type == 'Forgot_password':
        email = request_data.get('email')
        if not email:
            return jsonify({'message': 'Missing required fields'}), 400
        # check email có trong db không
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            check_query = "SELECT user_id FROM users WHERE user_email = %s"
            cursor.execute(check_query, (email,))  # Thêm dấu phẩy
            existing_user = cursor.fetchone()
            if not existing_user:
                return jsonify({'message': 'Email không tồn tại'}), 400
        except mysql.connector.Error as err:
            return jsonify({'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()

        #tạo dãy số ngẫu nhiên rồi gửi vào mail
        otp = random.randint(1000, 9999)
        send_email("MONEY APP", f"Mã OTP của bạn là: {otp}\n cảm ơn bạn đã sử dụng ứng dụng của chúng tôi", email)
        response_data = {
            'message': 'OTP sent successfully!',
            'otp': otp
        }
        return jsonify(response_data)

    elif request_type == 'update_password':
        email = request_data.get('email')
        password = request_data.get('password')
        if not email or not password:
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            update_query = """
            UPDATE users SET user_password = %s WHERE user_email = %s
            """
            cursor.execute(update_query, (password, email))
            conn.commit()

            response_data = {
                'message': 'Password updated successfully!'
            }
        except mysql.connector.Error as err:
            return jsonify({'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify(response_data)



    elif request_type == 'update_wallet':
        user_id = request_data.get('user_id')
        wallet = request_data.get('wallet')
        if not user_id or not wallet:
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            update_query = """
            UPDATE users SET wallet = %s WHERE user_id = %s
            """
            cursor.execute(update_query, (wallet, user_id))
            conn.commit()
            update_amount(user_id)
            response_data = {
                'message': 'Wallet updated successfully!'
            }
        except mysql.connector.Error as err:
            return jsonify({'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify(response_data)

    elif request_type == 'signup':
        name = request_data.get('name')  # Thay đổi từ 'username' thành 'name'
        password = request_data.get('password')
        email = request_data.get('email')
        print(f"Received signup request: name={name}, email={email}")  # Logging
        if not name or not password or not email:
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            check_query = "SELECT user_id FROM users WHERE user_email = %s"
            cursor.execute(check_query, (email,))  # Thêm dấu phẩy
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Email đã được sử dụng'}), 400
            insert_query = "INSERT INTO users (user_name, user_password, user_email) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (name, password, email))
            conn.commit()
            print(f"User registered successfully: name={name}, email={email}")  # Logging
            return jsonify({'message': 'User registered successfully!'})
        except mysql.connector.Error as err:
            print(f"Database error: {err}")  # Logging
            return jsonify({'message': f'Database error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()


    elif request_type == 'signin':
        email = request_data.get('email')
        password = request_data.get('password')
        # print(email, password)
        if not email or not password:
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            select_query = """
                    SELECT user_id FROM users
                    WHERE user_email = %s AND user_password = %s
                    """
            cursor.execute(select_query, (email, password))
            user = cursor.fetchone()
            # print(user)
            if user:
                # print("vô")
                select_user = """select amount, user_email, user_name, wallet ,user_password from users where user_id = %s"""
                cursor.execute(select_user, (user[0],))
                amount = cursor.fetchone()
                # select_transaction = """select transaction_id, transaction_amount, category_id, date, description, transaction_type from transactions where user_id = %s"""
                # cursor.execute(select_transaction, (user[0],))
                # transactions = cursor.fetchall()
                # print("lay giao dịch")
                transactions_list = get_transactions(user[0])
                # for transaction in transactions:
                #     transactions_list.append({
                #         "transaction_id": transaction[0],
                #         "amount": transaction[1],
                #         "category_id": transaction[2],
                #         "date": transaction[3].strftime('%Y-%m-%d'),  # Định dạng ngày tháng
                #         "description": transaction[4],
                #         "transaction_type": transaction[5]
                #     })
                # select_categories = """select category_id, category_name, category_icon, category_type from categories where user_id = %s"""
                # cursor.execute(select_categories, (user[0],))
                # categories = cursor.fetchall()
                # print("lay danh muc")
                categories_list = get_categories(user[0])
                # for category in categories:
                #     categories_list.append({
                #         "category_id": category[0],
                #         "category_name": category[1],
                #         "category_icon": category[2],
                #         "category_type": category[3]
                #     })

                response_data = {
                    'message': 'User logged in successfully!',
                    'user_id': user[0],
                    "amount": amount[0],
                    "user_email": amount[1],
                    "user_name": amount[2],
                    "transactions": transactions_list,
                    "categories": categories_list,
                    "wallet": amount[3],
                    "user_password": amount[4]
                }

            else:
                response_data = {
                    'message': 'Tài khoản hoặc mật khẩu không đúng'
                }
        except mysql.connector.Error as err:
            return jsonify({'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()

        return jsonify(response_data)



    # elif request_type == 'insert_categories':
    #     icon_name = request_data.get('category_icon')
    #     categories_name = request_data.get('category_name')
    #     categories_type = request_data.get('category_type')
    #     user_id = request_data.get('user_id')
    #     print(icon_name, categories_name, categories_type, user_id)
    #     # print("vô đây")
    #     if not icon_name or not categories_name or not user_id:
    #         return jsonify({'message': 'Missing required fields'}), 400
    #
    #     try:
    #         conn = mysql.connector.connect(**db_config)
    #         cursor = conn.cursor()
    #
    #         insert_query = """
    #                 INSERT INTO categories (category_name, category_icon, user_id, category_type)
    #                 VALUES (%s, %s, %s, %s)
    #                 """
    #         cursor.execute(insert_query, (categories_name,icon_name, user_id, categories_type))
    #         conn.commit()
    #
    #         response_data = get_categories(user_id)
    #     except mysql.connector.Error as err:
    #         return jsonify({'message': f'Error: {err}'}), 500
    #     finally:
    #         cursor.close()
    #         conn.close()
    #
    #     return jsonify(response_data)

    elif request_type == 'insert_categories':
        icon_name = request_data.get('category_icon')
        categories_name = request_data.get('category_name')
        categories_type = request_data.get('category_type')
        user_id = request_data.get('user_id')
        # print("vô đây")
        if not icon_name or not categories_name or not user_id:
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            insert_query = """
                        INSERT INTO categories (category_name, category_icon, user_id, category_type)
                        VALUES (%s, %s, %s, %s)
                        """
            cursor.execute(insert_query, (categories_name, icon_name, user_id, categories_type))
            conn.commit()

            select_user = """select amount, user_email, user_name, wallet from users where user_id = %s"""
            cursor.execute(select_user, (user_id,))
            amount = cursor.fetchone()

            transactions_list = get_transactions(user_id)

            categories_list = get_categories(user_id)

            response_data = {
                'message': 'User logged in successfully!',
                'user_id': user_id,
                "amount": amount[0],
                "user_email": amount[1],
                "user_name": amount[2],
                "transactions": transactions_list,
                "categories": categories_list,
                "wallet": amount[3]
            }
        except mysql.connector.Error as err:
            return jsonify({'message': f'Error: {err}'}), 500
        finally:
            cursor.close()
            conn.close()
        # print(response_data)
        return jsonify(response_data)
    elif request_type == 'getlist_categories':
        user_id = request_data.get('user_id')
        if not user_id:
            return jsonify({'message': 'Missing required fields'}), 400

        response_data = get_categories(user_id)
        return response_data
    else:
        return jsonify({'message': 'Invalid request type'}), 400



    # # Lấy dữ liệu từ request
    # request_data = request.json
    #
    # # Trích xuất URL của ảnh từ request_data
    # image_url = request_data.get('image_url')
    # if not image_url:
    #     return jsonify({'message': 'Image URL not provided'}), 400
    #
    # # Tải ảnh từ URL
    # image = download_image_from_url(image_url)
    # if image is None:
    #     return jsonify({'message': 'Failed to download image'}), 400
    #
    # # Trích xuất văn bản từ hình ảnh
    # extracted_text = extract_text_from_image(image)
    # # print("Extracted Text:", extracted_text)
    #
    # # Tạo prompt cho mô hình GenAI
    # prompt = ("tôi có một hóa đơn tính tiền được OCR ra nhưng bị lỗi chữ, hãy giúp tôi hoàn thành các câu và từ còn sai rồi trích xuất những thông tin trong hóa đơn nếu có: "
    #           "tổ chức lập hóa đơn, ngày lập hóa đơn, tên sản phẩm, số lượng mỗi sản phẩm, price, tổng số tiền thanh toán: "
    #           "(chú ý: trả lời đúng những mục tôi yêu cầu không thêm bớt và trả về dạng JSON, các key không dấu)")
    #
    # # Tương tác với mô hình GenAI
    # gemini_response = interact_with_gemini(prompt + "\n" + extracted_text)
    # print("Gemini Response:", gemini_response)
    # # Chuẩn bị dữ liệu phản hồi cho client
    # jsontext = convert_to_json(gemini_response)
    # response_data = {
    #     'message': 'Processed the image and extracted text successfully!',
    #     'gemini_response': jsontext
    #
    # }
    #
    # print("Response Data:", type(jsontext))
    # return (response_data)

# Chạy ứng dụng trên địa chỉ IP nội bộ và cổng mặc định là 5000
if __name__ == '__main__':
    app.run(host='192.168.2.23', port=5000)
