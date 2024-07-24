import cv2
import numpy as np
from PIL import Image, ImageEnhance

# Load the image using PIL
image_path = "D:\\THUCTAP\\images\\9.png"
image = Image.open(image_path)

# Convert the image to grayscale
gray_image = image.convert('L')

# Enhance the contrast
enhancer = ImageEnhance.Contrast(gray_image)
contrasted_image = enhancer.enhance(2)  # Increase the contrast by a factor of 2

# Convert the PIL image to a numpy array
image_np = np.array(contrasted_image)

# Sharpen the image
kernel_sharpening = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
sharpened_image = cv2.filter2D(image_np, -1, kernel_sharpening)

# Use OpenCV to apply a binary threshold
_, binary_image = cv2.threshold(sharpened_image, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Use OpenCV to reduce noise
denoised_image = cv2.fastNlMeansDenoising(binary_image, None, 30, 7, 21)

# Convert the processed image back to PIL format
final_image = Image.fromarray(denoised_image)

# Save the processed image
final_image.save("D:\\THUCTAP\\images\\10.png")

# Display the processed image (optional)
final_image.show()
