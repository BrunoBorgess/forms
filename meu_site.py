import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request, redirect, render_template, flash, url_for, session
from flask_mail import Mail
from werkzeug.utils import secure_filename




app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'uploads'
UPLOAD_FOLDER_2 = 'upload2'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_2'] = UPLOAD_FOLDER_2
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_2, exist_ok=True)

# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'lucasford677@gmail.com'
app.config['MAIL_PASSWORD'] = 'wess hvyi nxzc pvgh'
app.config['MAIL_DEFAULT_SENDER'] = 'lucasford677@gmail.com'
mail = Mail(app)



# Configuração do Tesseract
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_path
# Definir o caminho correto para os arquivos de idioma do Tesseract
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# Funções para processar o PDF e extrair CPF e nome
def crop_cpf_region(image):
    cpf_region = image.crop((588, 695, 777, 730))
    scale_factor = 3
    cpf_region = cpf_region.resize(
        (cpf_region.width * scale_factor, cpf_region.height * scale_factor),
        Image.Resampling.LANCZOS
    )
    cpf_region.save('cpf_region_debug.png')
    return cpf_region

def crop_name_region(image):
    name_region = image.crop((304, 454, 929, 489))
    scale_factor = 3
    name_region = name_region.resize(
        (name_region.width * scale_factor, name_region.height * scale_factor),
        Image.Resampling.LANCZOS
    )
    name_region.save('name_region_debug.png')
    return name_region

def preprocess_image(image):
    gray_image = image.convert('L')
    gray_image.save("preprocessed_region.png")
    return gray_image

def extract_cpf_from_image(image):
    cpf_image = crop_cpf_region(image)
    cpf_image = preprocess_image(cpf_image)
    text = pytesseract.image_to_string(
        cpf_image, config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-'
    )
    cleaned_text = ''.join(c for c in text if c.isdigit() or c in '.-')
    cpf_pattern = r'\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}'
    cpf_match = re.search(cpf_pattern, cleaned_text)
    return cpf_match.group(0) if cpf_match else "CPF não encontrado"

def extract_name_from_image(image):
    name_image = crop_name_region(image)
    name_image = preprocess_image(name_image)
    text = pytesseract.image_to_string(name_image, config='--oem 3 --psm 7')
    cleaned_text = text.strip()
    return cleaned_text if cleaned_text else "Nome não encontrado"

def convert_pdf_to_image_with_fitz(pdf_path, output_path):
    try:
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[0]
        pix = page.get_pixmap(dpi=300)
        image_path = os.path.join(output_path, "page_1.png")
        pix.save(image_path)
        pdf_document.close()
        return image_path
    except Exception as e:
        print(f"Erro ao converter PDF para imagem: {e}")
        return None

def process_pdf(pdf_path):
    output_path = "./uploads"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    image_path = convert_pdf_to_image_with_fitz(pdf_path, output_path)
    if not image_path:
        return "Erro ao converter o PDF para imagem."

    image = Image.open(image_path)
    cpf = extract_cpf_from_image(image)
    name = extract_name_from_image(image)

    return cpf, name

# Função para validar se os dados extraídos do PDF correspondem ao formulário
def validate_pdf_data(pdf_cpf, pdf_nome, form_cpf, form_nome):
    """
    Compara os dados extraídos do PDF com os dados fornecidos no formulário.
    Retorna True se os dados coincidirem, caso contrário False.
    """
    # Ignora pontuações e espaços ao comparar CPF e Nome
    cleaned_pdf_cpf = re.sub(r'\D', '', pdf_cpf)
    cleaned_form_cpf = re.sub(r'\D', '', form_cpf)

    # Converte tanto o nome extraído do PDF quanto o nome fornecido no formulário para maiúsculo
    cleaned_pdf_nome = re.sub(r'\s+', '', pdf_nome.strip().upper())
    cleaned_form_nome = re.sub(r'\s+', '', form_nome.strip().upper())

    if cleaned_pdf_cpf != cleaned_form_cpf:
        return False, "O CPF informado não corresponde ao CPF extraído do PDF."
    if cleaned_pdf_nome != cleaned_form_nome:
        return False, "O nome informado não corresponde ao nome extraído do PDF."
    return True, "Dados validados"


# 🟢 Função para apagar arquivos após envio
def clear_folder(folder_path):
    """Remove todos os arquivos dentro da pasta especificada."""
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, file))

import os
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import flash

# 🟢 Função para listar arquivos na pasta de uploads
def get_uploaded_files(folder_path):
    """Retorna a lista de arquivos no diretório especificado."""
    if not os.path.exists(folder_path):
        return []
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

# 🟢 Função para enviar e-mail com anexos
def send_email(nome, nascimento, cpf, rg, pis, endereco, cep, cidade, estado,
            celular, email, estado_civil, raca_cor, camisa_social, camisa_polo,
            primeiro_emprego, vale_transporte, cnh_path, imagemBase64, validation_message):
    
    sender_email = "lucasford677@gmail.com"
    sender_password = "wess hvyi nxzc pvgh"
    receiver_email = "lucasb.empreendimentos@gmail.com"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Formulário de Emprego"

    # Corpo do e-mail
    body = f"""
    ✅ {validation_message}
    <p><strong>Nome Completo:</strong> {nome}</p>
    <p><strong>Data de Nascimento:</strong> {nascimento}</p>
    <p><strong>CPF:</strong> {cpf}</p>
    <p><strong>RG:</strong> {rg}</p>
    <p><strong>PIS:</strong> {pis}</p>
    <p><strong>Endereço:</strong> {endereco}</p>
    <p><strong>CEP:</strong> {cep}</p>
    <p><strong>Cidade:</strong> {cidade}</p>
    <p><strong>Estado:</strong> {estado}</p>
    <p><strong>Celular:</strong> {celular}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Estado Civil:</strong> {estado_civil}</p>
    <p><strong>Raça/Cor:</strong> {raca_cor}</p>
    <p><strong>Uniforme Camisa Social:</strong> {camisa_social}</p>
    <p><strong>Uniforme Polo:</strong> {camisa_polo}</p>
    <p><strong>Primeiro Emprego:</strong> {primeiro_emprego}</p>
    <p><strong>Vale transporte:</strong> {vale_transporte}</p>
    """
    msg.attach(MIMEText(body, 'html'))

    # 🟢 Anexar CNH
    if cnh_path:
        with open(cnh_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(cnh_path)}")
            msg.attach(part)

    # 🟢 Anexar a imagem capturada (se existir)
    if imagemBase64:
        try:
            imagemBase64 = imagemBase64.split(",")[1]  # Remove o prefixo 'data:image/png;base64,'
            imagem_bytes = base64.b64decode(imagemBase64)

            temp_image_path = "uploads/cnh_capturada.png"
            with open(temp_image_path, "wb") as f:
                f.write(imagem_bytes)

            with open(temp_image_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(temp_image_path)}")
                msg.attach(part)

            # Apagar a imagem temporária após envio
            os.remove(temp_image_path)

        except Exception as e:
            flash(f"Erro ao processar a imagem capturada: {e}", "danger")

    # 🟢 Anexar arquivos do Step 2
    for file_path in get_uploaded_files(app.config['UPLOAD_FOLDER_2']):
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())  # Lê o arquivo
            encoders.encode_base64(part)  # Converte para Base64 (formato seguro para envio)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file_path)}")  # Define o nome do anexo
            msg.attach(part)  # Anexa o arquivo ao e-mail

    # 🟢 Enviar o e-mail
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        flash("Formulário enviado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao enviar o e-mail: {e}", "danger")

    # 🟢 Apagar arquivos após o envio
    clear_folder(app.config['UPLOAD_FOLDER'])
    clear_folder(app.config['UPLOAD_FOLDER_2'])

# 🟢 Rota principal do formulário
@app.route("/", methods=["GET", "POST"])
def form():
    if "step" not in session:
        session["step"] = 1

    if request.method == "POST":
        if session["step"] == 1:
            session.update(request.form.to_dict())
            session["step"] = 2
            return redirect(url_for("form"))

        elif session["step"] == 2:
            cnh_file = request.files.get("cnh")
            cnh_path = None

            if cnh_file and cnh_file.filename:
                filename = secure_filename(cnh_file.filename)
                cnh_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                cnh_file.save(cnh_path)

                # 🟢 Chama as funções para extrair Nome e CPF da imagem
                image = Image.open(cnh_path)
                pdf_cpf = extract_cpf_from_image(image)
                pdf_nome = extract_name_from_image(image)

                # 🟢 Validação: Somente envia o e-mail se CPF e Nome forem válidos
                if pdf_cpf != "CPF não encontrado" and pdf_nome != "Nome não encontrado":
                    session_data = {key: value for key, value in session.items() if key != "step"}

                    # 🟢 Salva os arquivos adicionais
                    for i in range(1, 21):
                        file = request.files.get(f"arquivo{i}")
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER_2'], filename))

                    # 🟢 Envia o e-mail
                    send_email(**session_data, cnh_path=cnh_path, validation_message="✅ Dados Validados")

                    session.clear()
                    return redirect(url_for("form"))
                else:
                    flash("❌ Erro: Nome ou CPF não foram encontrados na CNH. Verifique e tente novamente.", "danger")
                    return redirect(url_for("form"))

    return render_template("form.html", step=session["step"])

if __name__ == "__main__":
    app.run(debug=True)
