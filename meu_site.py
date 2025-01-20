import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from flask import Flask, redirect, url_for, session

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
        cidade = request.form.get("cidade")
        estado = request.form.get("estado")
        celular = request.form.get("celular")
        email = request.form.get("email")
        # radius button
        estado_civil = request.form.get("estado_civil")
        raca_cor = request.form.get("raca_cor")
        camisa_social = request.form.get("camisa_social")
        camisa_polo = request.form.get("camisa_polo")
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
                nome, nascimento, cpf, rg, pis, endereco, cep, cidade, estado, 
                celular, email, estado_civil, raca_cor, camisa_social, 
                camisa_polo, primeiro_emprego, cnh_path
            )
            flash("Formulário enviado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao enviar o formulário: {e}", "danger")

        return redirect(url_for("form"))
    
    return render_template("form.html")



def send_email(nome, nascimento, cpf, rg, pis, endereco, cep, cidade, estado,
            celular, email, estado_civil, raca_cor, camisa_social,
            camisa_polo, primeiro_emprego, cnh_path):
    sender_email = "lucasford677@gmail.com"  # E-mail do remetente
    sender_password = "wess hvyi nxzc pvgh"  # Senha do remetente ou senha de app
    receiver_email = "lucasb.empreendimentos@gmail.com"  # E-mail de destino

    # Montar o email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Formulário de Emprego"

    body = f"""
    Nome Completo: {nome}
    Data de Nascimento: {nascimento}
    CPF: {cpf}
    RG: {rg}
    PIS: {pis}
    Endereço: {endereco}
    CEP: {cep}
    Cidade: {cidade}
    Estado: {estado}
    Celular: {celular}
    Email: {email}
    Estado Civil: {estado_civil}
    Raça/Cor: {raca_cor}
    Uniforme Camisa Social: {camisa_social}
    Uniforme Polo: {camisa_polo}
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

    try:
        # Conectar ao servidor SMTP do Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Inicia o TLS para segurança
            server.login(sender_email, sender_password)  # Login na conta do Gmail
            server.send_message(msg)  # Envia a mensagem

    except Exception as e:
        print(f"Erro ao enviar o email: {e}")

    # Remover o arquivo temporário (se houver)
    if cnh_path:
        os.remove(cnh_path)


if __name__ == "__main__":
    app.run(debug=True)


    # wess hvyi nxzc pvgh