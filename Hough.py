import rasterio
from rasterio.plot import reshape_as_image
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Paths for the TIF file and the output PNG file
tif_path = "clipped.tif"  # Replace with your TIF file path
png_path = "clipped_converted.png"

def normalize_image(image):
    """
    Normalize image values to enhance brightness and contrast,
    handling outlier values for better visualization.
    """
    # Clip to percentile range to handle outliers
    min_percentile = np.percentile(image, 2)
    max_percentile = np.percentile(image, 98)
    clipped_image = np.clip(image, min_percentile, max_percentile)
    
    # Normalize to range 0-255
    normalized_image = ((clipped_image - min_percentile) / (max_percentile - min_percentile) * 255).astype(np.uint8)
    return normalized_image

# Normalize the image data
with rasterio.open(tif_path) as src:
    tif_image = reshape_as_image(src.read())
    normalized_tif_image = normalize_image(tif_image)

# Save the normalized image as PNG
cv2.imwrite(png_path, normalized_tif_image)

# Load the normalized PNG image
imagem = cv2.imread(png_path, cv2.IMREAD_COLOR)
imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

# Smooth the image to reduce noise
imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (9, 9), 0)

# Detect circles using the Hough Transform
circulos = cv2.HoughCircles(imagem_suavizada, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                            param1=100, param2=30, minRadius=5, maxRadius=70)

# Draw the detected circles
imagem_circulos = imagem_rgb.copy()
if circulos is not None:
    circulos = np.uint16(np.around(circulos))
    for i in circulos[0, :]:
        cv2.circle(imagem_circulos, (i[0], i[1]), i[2], (0, 255, 0), 2)  # Outer circle
        cv2.circle(imagem_circulos, (i[0], i[1]), 2, (0, 0, 255), 3)     # Center

# Count the number of detected circles
numero_de_pivos = len(circulos[0]) if circulos is not None else 0

# Show the original and resulting images
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.title('Imagem Original Normalizada')
plt.imshow(imagem_rgb)
plt.axis('off')
plt.subplot(1, 2, 2)
plt.title('Detecção de Pivôs de Irrigação')
plt.imshow(imagem_circulos)
plt.axis('off')
plt.show()

# Print the number of detected pivots
print(f"Número de pivôs detectados: {numero_de_pivos}")
