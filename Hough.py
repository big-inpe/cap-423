# Carregar a imagem de satélite
imagem = cv2.imread('pivo_cristalina.png')
imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

# Suavizar a imagem para reduzir ruídos
imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (9, 9), 0)

# Detectar círculos usando a Transformada de Hough
circulos = cv2.HoughCircles(imagem_suavizada, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                            param1=100, param2=30, minRadius=5, maxRadius=70)

# Desenhar os círculos detectados
imagem_circulos = imagem_rgb.copy()
if circulos is not None:
    circulos = np.uint16(np.around(circulos))
    for i in circulos[0, :]:
        cv2.circle(imagem_circulos, (i[0], i[1]), i[2], (0, 255, 0), 2)
        cv2.circle(imagem_circulos, (i[0], i[1]), 2, (0, 0, 255), 3)

# Mostrar imagem original e resultado
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.title('Imagem Original')
plt.imshow(imagem_rgb)
plt.subplot(1, 2, 2)
plt.title('Detecção de Pivôs de Irrigação')
plt.imshow(imagem_circulos)
plt.show()

# Contar o número de pivôs detectados
numero_de_pivos = len(circulos[0]) if circulos is not None else 0
print(f"Número de pivôs detectados: {numero_de_pivos}")