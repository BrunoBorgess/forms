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

# 🟢 Funções para processar CNH
def process_pdf(pdf_path):
    """Extrai CPF e Nome da CNH em PDF."""
    try:
        doc = fitz.open(pdf_path)
        pix = doc[0].get_pixmap(dpi=300)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], "cnh_temp.png")
        pix.save(image_path)
        doc.close()

        image = Image.open(image_path)
        cpf = extract_cpf_from_image(image)
        name = extract_name_from_image(image)
        return cpf, name
    except Exception as e:
        print(f"Erro ao processar a CNH: {e}")
        return "Erro ao processar", "Erro ao processar"

def extract_cpf_from_image(image):
    """Extrai CPF da imagem da CNH."""
    cpf_pattern = r'\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}'
    text = pytesseract.image_to_string(image, config='--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.-')
    match = re.search(cpf_pattern, text)
    return match.group(0) if match else "CPF não encontrado"

def extract_name_from_image(image):
    """Extrai Nome da imagem da CNH."""
    text = pytesseract.image_to_string(image, config='--oem 3 --psm 7')
    return text.strip() if text else "Nome não encontrado"

def validate_pdf_data(pdf_cpf, pdf_nome, form_cpf, form_nome):
    """Compara os dados extraídos da CNH com os informados no formulário."""
    return re.sub(r'\D', '', pdf_cpf) == re.sub(r'\D', '', form_cpf) and pdf_nome.lower().strip() == form_nome.lower().strip()

# 🟢 Função para listar arquivos em uma pasta
def get_uploaded_files(directory):
    """Retorna lista de arquivos dentro da pasta especificada."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

# 🟢 Função para apagar arquivos após envio
def clear_folder(folder_path):
    """Remove todos os arquivos dentro da pasta especificada."""
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, file))

# 🟢 Função para enviar e-mail com anexos
def send_email(nome, nascimento, cpf, rg, pis, endereco, cep, cidade, estado,
            celular, email, estado_civil, raca_cor, camisa_social, camisa_polo,
            primeiro_emprego, vale_transporte, cnh_path, validation_message):
    
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

    # 🟢 Anexar arquivos do Step 2
    for file_path in get_uploaded_files(app.config['UPLOAD_FOLDER_2']):
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file_path)}")
            msg.attach(part)

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

            for i in range(1, 21):
                file = request.files.get(f"arquivo{i}")
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_2'], filename))

            session_data = {key: value for key, value in session.items() if key != "step"}
            send_email(**session_data, cnh_path=cnh_path, validation_message="Dados Validados")
            session.clear()
            return redirect(url_for("form"))

    return render_template("form.html", step=session["step"])

if __name__ == "__main__":
    app.run(debug=True)
