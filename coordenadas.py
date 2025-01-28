import cv2

# Função para capturar as coordenadas do clique na imagem
def get_coordinates(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f'Coordenadas: ({x}, {y})')

# Carregar a imagem
image_path = 'pdf-test/page_1.png'
image = cv2.imread(image_path)

# Exibir a imagem
cv2.imshow('Clique na imagem para pegar coordenadas', image)

# Configurar o mouse para pegar as coordenadas
cv2.setMouseCallback('Clique na imagem para pegar coordenadas', get_coordinates)

# Aguardar que o usuário clique na imagem
cv2.waitKey(0)

# Fechar a janela após o clique
cv2.destroyAllWindows()
