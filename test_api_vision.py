import os
from google.cloud import vision
import io

def detect_text(path):
    """Detects text in the file."""
    # Thiết lập biến môi trường cho Google Application Credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:\THUCTAP\\virtual-aileron-425501-m5-c0c8cb19b03d.json"

    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    print('Texts:')
    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(response.error.message))

# Gọi hàm detect_text với một tệp hình ảnh


detect_text("D:\THUCTAP\images\\10.png")
