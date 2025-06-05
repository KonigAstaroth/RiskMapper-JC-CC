from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.mail import send_mail
import ssl
import smtplib

def sendEmail(email):
    sender = 'roboed3dguillermo@gmail.com'
    sender_pass = 'qqwypqyqgudgecah'
    receiver = email
    subject = "Restablecer contraseña"
    body = """Para restablecer su contraseña, haga click en el siguiente link: http://127.0.0.1:8000/recoverPass/"""

    conexion = get_connection(
        host='smtp.gmail.com',
        port=465,
        username=sender,
        password=sender_pass,
        use_ssl=True
    )

    mensaje = EmailMessage(
        subject=subject,
        body=body,
        from_email=sender,
        to=[receiver],
        connection=conexion,
    )

    # Enviar
    mensaje.send()

    
