import requests
import json

# Địa chỉ IP và cổng của server Flask
url = 'http://192.168.2.51:5000/api'

# Dữ liệu muốn gửi đi (ví dụ)
data_to_send = {'key': 'value'}

# Gửi yêu cầu POST tới server Flask
response = requests.post(url, json=data_to_send)

# Kiểm tra và xử lý phản hồi từ server
if response.status_code == 200:
    print("Request successful!")
    print("Response from server:")
    print(json.dumps(response.json(), indent=2))  # In ra nội dung của phản hồi
else:
    print("Request failed with status code:", response.status_code)
