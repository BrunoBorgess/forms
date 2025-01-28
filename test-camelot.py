import os
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
# Caminho para o executável do Tesseract
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Caminho para a pasta tessdata
tessdata_prefix = r"C:\Program Files\Tesseract-OCR\tessdata"

# Configura as variáveis de ambiente corretamente
os.environ['TESSDATA_PREFIX'] = tessdata_prefix
pytesseract.pytesseract.tesseract_cmd = tesseract_path







'''
# Terceira função de teste pegando o nome e o cpf - a que deu mais certo até o momento 
from PIL import Image
import pytesseract
import re

def crop_cpf_region(image):
    """
    Recorta a região do CPF na imagem e amplia a resolução.
    :param image: Objeto PIL.Image.
    :return: Região do CPF ampliada.
    """
    # Coordenadas do recorte (ajustar conforme necessário)
    cpf_region = image.crop((209, 242, 400, 261))  # Ajustar com base no layout da imagem

    # Ampliar a resolução do recorte para facilitar o OCR
    scale_factor = 3  # Fator de ampliação (3x maior)
    cpf_region = cpf_region.resize(
        (cpf_region.width * scale_factor, cpf_region.height * scale_factor),
        Image.Resampling.LANCZOS
    )

    # Salvar para verificação
    cpf_region.save('cpf_region_debug.png')
    return cpf_region

def crop_name_region(image):
    """
    Recorta a região do nome completo na imagem e amplia a resolução.
    :param image: Objeto PIL.Image.
    :return: Região do nome completa ampliada.
    """
    # Coordenadas do recorte 
    name_region = image.crop((108, 157, 333, 168))  # Ajustar com base no layout da imagem

    # Ampliar a resolução do recorte para facilitar o OCR
    scale_factor = 3  # Fator de ampliação (3x maior)
    name_region = name_region.resize(
        (name_region.width * scale_factor, name_region.height * scale_factor),
        Image.Resampling.LANCZOS
    )

    # Salvar para verificação
    name_region.save('name_region_debug.png')
    return name_region

def preprocess_image(image):
    """
    Pré-processa a imagem para o OCR, preservando a resolução e legibilidade.
    :param image: Objeto PIL.Image.
    :return: Imagem pré-processada.
    """
    # Apenas converter para escala de cinza, sem reduzir a qualidade
    gray_image = image.convert('L')  # Converter para tons de cinza
    gray_image.save("preprocessed_region.png")  # Salvar para depuração
    return gray_image

def extract_cpf_from_image(image_path):
    """
    Extrai o CPF de uma imagem fornecida.
    :param image_path: Caminho para a imagem.
    :return: CPF extraído ou mensagem de erro.
    """
    try:
        # Carregar a imagem completa
        image = Image.open(image_path)

        # Recortar a região onde o CPF está localizado
        cpf_image = crop_cpf_region(image)

        # Pré-processar a região recortada (mantendo a resolução)
        cpf_image = preprocess_image(cpf_image)

        # Realizar OCR na imagem pré-processada
        text = pytesseract.image_to_string(
            cpf_image, 
            config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-'
        )
        print(f"Texto extraído (bruto - CPF):\n{text}")  # Debug do texto extraído

        # Limpar texto extraído (manter apenas números, pontos e traços)
        cleaned_text = ''.join(c for c in text if c.isdigit() or c in '.-')
        print(f"Texto limpo para busca do CPF:\n{cleaned_text}")  # Debug do texto limpo

        # Buscar padrão de CPF no texto limpo
        cpf_pattern = r'\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}'
        cpf_match = re.search(cpf_pattern, cleaned_text)

        if cpf_match:
            return cpf_match.group(0)  # Retorna o CPF encontrado
        return "CPF não encontrado"

    except Exception as e:
        return f"Erro durante a extração do CPF: {e}"

def extract_name_from_image(image_path):
    """
    Extrai o nome completo de uma imagem fornecida.
    :param image_path: Caminho para a imagem.
    :return: Nome completo extraído ou mensagem de erro.
    """
    try:
        # Carregar a imagem completa
        image = Image.open(image_path)

        # Recortar a região onde o nome está localizado
        name_image = crop_name_region(image)

        # Pré-processar a região recortada (mantendo a resolução)
        name_image = preprocess_image(name_image)

        # Realizar OCR na imagem pré-processada
        text = pytesseract.image_to_string(
            name_image, 
            config='--oem 3 --psm 7'
        )
        print(f"Texto extraído (bruto - Nome):\n{text}")  # Debug do texto extraído

        # Limpar texto extraído
        cleaned_text = text.strip()
        return cleaned_text if cleaned_text else "Nome não encontrado"

    except Exception as e:
        return f"Erro durante a extração do nome: {e}"

# Caminho para a imagem
image_path = 'pdf-test/cnh-novo.png'

# Extração do CPF
cpf = extract_cpf_from_image(image_path)
print(f"CPF encontrado: {cpf}")

# Extração do Nome
nome = extract_name_from_image(image_path)
print(f"Nome encontrado: {nome}")
'''



# QUARTO TESTE - CONVERTENDO PDF

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import re
import os


def crop_cpf_region(image):
    """
    Recorta a região do CPF na imagem e amplia a resolução.
    """
    cpf_region = image.crop((588, 695, 777, 730))
    scale_factor = 3
    cpf_region = cpf_region.resize(
        (cpf_region.width * scale_factor, cpf_region.height * scale_factor),
        Image.Resampling.LANCZOS
    )
    cpf_region.save('cpf_region_debug.png')
    return cpf_region


def crop_name_region(image):
    """
    Recorta a região do nome na imagem e amplia a resolução.
    """
    name_region = image.crop((304, 454, 929, 489))
    scale_factor = 3
    name_region = name_region.resize(
        (name_region.width * scale_factor, name_region.height * scale_factor),
        Image.Resampling.LANCZOS
    )
    name_region.save('name_region_debug.png')
    return name_region


def preprocess_image(image):
    """
    Pré-processa a imagem para melhorar o OCR.
    """
    gray_image = image.convert('L')
    gray_image.save("preprocessed_region.png")
    return gray_image


def extract_cpf_from_image(image):
    """
    Extrai o CPF de uma imagem.
    """
    cpf_image = crop_cpf_region(image)
    cpf_image = preprocess_image(cpf_image)
    text = pytesseract.image_to_string(
        cpf_image, config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-'
    )
    print(f"Texto extraído (bruto - CPF):\n{text}")
    cleaned_text = ''.join(c for c in text if c.isdigit() or c in '.-')
    print(f"Texto limpo para busca do CPF:\n{cleaned_text}")
    cpf_pattern = r'\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}'
    cpf_match = re.search(cpf_pattern, cleaned_text)
    return cpf_match.group(0) if cpf_match else "CPF não encontrado"


def extract_name_from_image(image):
    """
    Extrai o nome completo de uma imagem.
    """
    name_image = crop_name_region(image)
    name_image = preprocess_image(name_image)
    text = pytesseract.image_to_string(name_image, config='--oem 3 --psm 7')
    print(f"Texto extraído (bruto - Nome):\n{text}")
    cleaned_text = text.strip()
    return cleaned_text if cleaned_text else "Nome não encontrado"


def convert_pdf_to_image_with_fitz(pdf_path, output_path):
    """
    Converte a primeira página de um PDF para imagem usando PyMuPDF (fitz).
    """
    try:
        pdf_document = fitz.open(pdf_path)  # Abre o PDF
        page = pdf_document[0]  # Obtém a primeira página
        pix = page.get_pixmap(dpi=300)  # Renderiza a página com 300 DPI
        image_path = os.path.join(output_path, "page_1.png")  # Caminho da imagem
        pix.save(image_path)  # Salva a imagem
        pdf_document.close()
        return image_path
    except Exception as e:
        print(f"Erro ao converter PDF para imagem: {e}")
        return None


def process_pdf(pdf_path):
    """
    Processo completo: Converte PDF em imagem e extrai CPF e Nome.
    """
    output_path = "./uploads"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    image_path = convert_pdf_to_image_with_fitz(pdf_path, output_path)
    if not image_path:
        return "Erro ao converter o PDF para imagem."

    # Carregar a imagem gerada
    image = Image.open(image_path)

    # Extrair informações
    cpf = extract_cpf_from_image(image)
    name = extract_name_from_image(image)

    return cpf, name


# Caminho do PDF na pasta uploads
pdf_path = './uploads/CNH-e.pdf.pdf'

# Verificar se o arquivo existe
if os.path.exists(pdf_path):
    cpf, name = process_pdf(pdf_path)
    print(f"CPF encontrado: {cpf}")
    print(f"Nome encontrado: {name}")
else:
    print("Arquivo PDF não encontrado na pasta uploads.")










