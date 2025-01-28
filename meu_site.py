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
from flask import Flask, request, redirect, render_template, flash, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Defina o caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Caminho usual no Render


# Ajuste para o caminho correto no servidor

# Caminho para o executável do Tesseract
#tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Caminho para a pasta tessdata
#tessdata_prefix = r"C:\Program Files\Tesseract-OCR\tessdata"

# Configura as variáveis de ambiente corretamente
os.environ['TESSDATA_PREFIX'] = pytesseract.pytesseract.tesseract_cmd
pytesseract.pytesseract.tesseract_cmd = pytesseract.pytesseract.tesseract_cmd

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

# Função para enviar o e-mail
def send_email(nome, nascimento, cpf, rg, pis, endereco, cep, cidade, estado,
            celular, email, estado_civil, raca_cor, camisa_social,
            camisa_polo, primeiro_emprego, vale_transporte, cnh_path, validation_message):
    sender_email = "lucasford677@gmail.com"
    sender_password = "wess hvyi nxzc pvgh"
    receiver_email = "lucasb.empreendimentos@gmail.com"

    # Estilo para a validação
    validation_style = """
    <div style="background-color: #4CAF50; color: white; padding: 10px; font-size: 16px; font-weight: bold; border-radius: 5px;">
        ✅ {validation_message}
    </div>
    """

    # Substituindo a variável `validation_message` pelo texto passado
    validation_message = validation_style.format(validation_message=validation_message)

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Formulário de Emprego"

    # Corpo do e-mail com a validação em verde no topo
    body = f"""
    {validation_message}
    <p>Nome Completo: {nome}</p>
    <p>Data de Nascimento: {nascimento}</p>
    <p>CPF: {cpf}</p>
    <p>RG: {rg}</p>
    <p>PIS: {pis}</p>
    <p>Endereço: {endereco}</p>
    <p>CEP: {cep}</p>
    <p>Cidade: {cidade}</p>
    <p>Estado: {estado}</p>
    <p>Celular: {celular}</p>
    <p>Email: {email}</p>
    <p>Estado Civil: {estado_civil}</p>
    <p>Raça/Cor: {raca_cor}</p>
    <p>Uniforme Camisa Social: {camisa_social}</p>
    <p>Uniforme Polo: {camisa_polo}</p>
    <p>Primeiro Emprego: {primeiro_emprego}</p>
    <p>Vale transporte: {vale_transporte}</p>
    """

    msg.attach(MIMEText(body, 'html'))  # Corpo agora é HTML

    if cnh_path:
        attachment = MIMEBase('application', 'octet-stream')
        with open(cnh_path, 'rb') as attachment_file:
            attachment.set_payload(attachment_file.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f"attachment; filename={os.path.basename(cnh_path)}")
        msg.attach(attachment)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

    except Exception as e:
        print(f"Erro ao enviar o email: {e}")

    if cnh_path:
        os.remove(cnh_path)


# Página inicial com o formulário
@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        nome = request.form.get("nome")
        nascimento = request.form.get("nascimento")
        cpf = request.form.get("cpf")
        rg = request.form.get("rg")
        pis = request.form.get("pis")
        endereco = request.form.get("endereco")
        cep = request.form.get("cep")
        cidade = request.form.get("cidade")
        estado = request.form.get("estado")
        celular = request.form.get("celular")
        email = request.form.get("email")
        estado_civil = request.form.get("estado_civil")
        raca_cor = request.form.get("raca_cor")
        camisa_social = request.form.get("camisa_social")
        camisa_polo = request.form.get("camisa_polo")
        primeiro_emprego = request.form.get("primeiro_emprego")
        vale_transporte = request.form.get("vale_transporte")

        cnh_file = request.files["cnh"]
        cnh_path = None
        if cnh_file:
            cnh_path = os.path.join(app.config['UPLOAD_FOLDER'], cnh_file.filename)
            cnh_file.save(cnh_path)

        # Processar o PDF
        validation_message = ""
        if cnh_path:
            pdf_cpf, pdf_nome = process_pdf(cnh_path)
            print(f"CPF detectado: {pdf_cpf}")
            print(f"Nome detectado: {pdf_nome}")

            # Validar CPF e Nome
            valid, validation_message = validate_pdf_data(pdf_cpf, pdf_nome, cpf, nome)
            if not valid:
                flash(validation_message, "danger")
                return redirect(url_for("form"))

        try:
            send_email(
                nome, nascimento, cpf, rg, pis, endereco, cep, cidade, estado,
                celular, email, estado_civil, raca_cor, camisa_social,
                camisa_polo, primeiro_emprego, vale_transporte, cnh_path, validation_message
            )
            flash("Formulário enviado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao enviar o formulário: {e}", "danger")

        return redirect(url_for("form"))

    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True)
