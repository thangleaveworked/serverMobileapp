import cv2
import numpy as np
from PIL import Image, ImageEnhance
import easyocr

# Load the image using PIL
image_path = "D:\\THUCTAP\\images\\5.png"
image = Image.open(image_path)

# Convert the image to grayscale
gray_image = image.convert('L')

# Enhance the contrast
enhancer = ImageEnhance.Contrast(gray_image)
contrasted_image = enhancer.enhance(2)  # Increase the contrast by a factor of 2

# Convert the PIL image to a numpy array
image_np = np.array(contrasted_image)

# Apply binary threshold
_, binary_image = cv2.threshold(image_np, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Use OpenCV to reduce noise
denoised_image = cv2.fastNlMeansDenoising(binary_image, None, 30, 7, 21)

# Initialize EasyOCR reader
reader = easyocr.Reader(['en', 'vi'])  # Initialize with English and Vietnamese languages

# Perform OCR to detect characters
result = reader.readtext(denoised_image)

# Create a mask for detected text regions
mask = np.zeros_like(denoised_image)

# Get bounding boxes for each character
for (bbox, text, prob) in result:
    (top_left, top_right, bottom_right, bottom_left) = bbox
    top_left = tuple(map(int, top_left))
    bottom_right = tuple(map(int, bottom_right))
    cv2.rectangle(mask, top_left, bottom_right, 255, -1)

# Sharpen the image within the masked regions
kernel_sharpening = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])

sharpened_image = cv2.filter2D(denoised_image, -1, kernel_sharpening, borderType=cv2.BORDER_CONSTANT)
enhanced_image = np.where(mask == 255, sharpened_image, denoised_image)

# Convert the processed image back to PIL format
final_image = Image.fromarray(enhanced_image)

# Save the processed image
# final_image.save("D:\\THUCTAP\\images\\processed_image.png")

# Display the processed image (optional)
final_image.show()

# Print the detected text
for (bbox, text, prob) in result:
    print(f'Detected Text: {text}, Probability: {prob}')
