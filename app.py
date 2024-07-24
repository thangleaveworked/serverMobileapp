from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

def send_email(subject, body, to_email):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "phanminhthangcode@gmail.com"  # Thay bằng email của bạn
    smtp_password = "jyga cpnz crxk oode"     # Thay bằng mật khẩu của bạn

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        print("Email đã được gửi thành công!")
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")
    finally:
        server.quit()

@app.route('/send-email', methods=['POST'])
def email_endpoint():
    data = request.get_json()
    to_email = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    print(to_email, subject, body)
    if not to_email or not subject or not body:
        return jsonify({'message': 'Thiếu thông tin cần thiết'}), 400

    try:
        send_email(subject, body, to_email)
        return jsonify({'message': 'Email đã được gửi thành công!'}), 200
    except Exception as e:
        return jsonify({'message': f'Lỗi khi gửi email: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)
