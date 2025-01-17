from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Página inicial com o formulário
@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # Capturar os dados do formulário
        nome = request.form.get("nome")
        nascimento = request.form.get("nascimento")
        cpf = request.form.get("cpf")
        rg = request.form.get("rg")
        pis = request.form.get("pis")
        endereco = request.form.get("endereco")
        cep = request.form.get("cep")
        cidade_estado = request.form.get("cidade_estado")
        celular = request.form.get("celular")
        email = request.form.get("email")
        estado_civil = request.form.get("estado_civil")
        raca_cor = request.form.get("raca_cor")
        uniforme_camisa = request.form.get("uniforme_camisa")
        uniforme_polo = request.form.get("uniforme_polo")
        primeiro_emprego = request.form.get("primeiro_emprego")
        
        # Salvar a foto da CNH
        cnh_file = request.files["cnh"]
        cnh_path = None
        if cnh_file:
            cnh_path = os.path.join(app.config['UPLOAD_FOLDER'], cnh_file.filename)
            cnh_file.save(cnh_path)
        
        # Enviar os dados para o email
        try:
            send_email(
                nome, nascimento, cpf, rg, pis, endereco, cep, cidade_estado, 
                celular, email, estado_civil, raca_cor, uniforme_camisa, 
                uniforme_polo, primeiro_emprego, cnh_path
            )
            flash("Formulário enviado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao enviar o formulário: {e}", "danger")

        return redirect(url_for("form"))
    
    return render_template("form.html")

def send_email(nome, nascimento, cpf, rg, pis, endereco, cep, cidade_estado,
            celular, email, estado_civil, raca_cor, uniforme_camisa,
            uniforme_polo, primeiro_emprego, cnh_path):
    sender_email = "seu_email"
    sender_password = "sua_senha"
    receiver_email = "lucasb.empreendimentos@gmail.com"

    # Montar o email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Formulário de Cadastro"

    body = f"""
    Nome Completo: {nome}
    Data de Nascimento: {nascimento}
    CPF: {cpf}
    RG: {rg}
    PIS: {pis}
    Endereço: {endereco}
    CEP: {cep}
    Cidade/Estado: {cidade_estado}
    Celular: {celular}
    Email: {email}
    Estado Civil: {estado_civil}
    Raça/Cor: {raca_cor}
    Uniforme Camisa Social: {uniforme_camisa}
    Uniforme Polo: {uniforme_polo}
    Primeiro Emprego: {primeiro_emprego}
    """

    msg.attach(MIMEText(body, 'plain'))

    # Anexar a CNH
    if cnh_path:
        attachment = MIMEBase('application', 'octet-stream')
        with open(cnh_path, 'rb') as attachment_file:
            attachment.set_payload(attachment_file.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f"attachment; filename={os.path.basename(cnh_path)}")
        msg.attach(attachment)

    # Enviar o email
    with smtplib.SMTP('lucasb.empreendimentos@gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

    # Remover o arquivo temporário
    if cnh_path:
        os.remove(cnh_path)

if __name__ == "__main__":
    app.run(debug=True)



