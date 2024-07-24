import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, body, to_email):
    # Thông tin tài khoản và máy chủ SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "phanminhthangcode@gmail.com"  # Thay bằng email của bạn
    smtp_password = "jyga cpnz crxk oode"     # Thay bằng mật khẩu của bạn

    # Tạo đối tượng email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject

    # Đính kèm phần nội dung email
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Kết nối đến máy chủ SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Bắt đầu mã hóa TLS
        server.login(smtp_user, smtp_password)  # Đăng nhập vào tài khoản

        # Gửi email
        server.sendmail(smtp_user, to_email, msg.as_string())
        print("Email đã được gửi thành công!")

    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")

    finally:
        server.quit()  # Đóng kết nối đến máy chủ SMTP

# Gửi email
send_email("đòi nợ", "ai là goat server", "21004173@st.vlute.edu.vn")
