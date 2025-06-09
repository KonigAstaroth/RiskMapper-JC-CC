from django.conf import settings
from django.core.mail import EmailMessage, get_connection, send_mail, EmailMultiAlternatives
from email.mime.image import MIMEImage
import os


def sendEmail(email, link):
    sender = 'roboed3dguillermo@gmail.com'
    sender_pass = 'qqwypqyqgudgecah'
    receiver = email
    subject = "Restablecer contraseña"
    body = """Para restablecer su contraseña, haga click en el siguiente link: http://127.0.0.1:8000/recoverPass/"""
    route_image = os.path.join(settings.BASE_DIR, 'app', 'static', 'images', 'eclipse-letterless.png')

    html_body = f"""
       
       <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
    </head>
    <body style="width: 100%; background-color: #dddddd;">
        <div id="email" style="margin:auto;">
            <table role="presentation" style="width: 100%;">
                <tr>
                    <td style="text-align: center; color: white; background-color: #202020; ">
                        <h1 style="font-family: 'Open Sans', Arial, sans-serif;">Eclipse Solutions</h1>
                    </td>
                </tr>
            </table>
            <h2 style="text-align: center; color: #202020;">El link para restablecer la contrasena ha sido generado</h2>
            <table role="presentation" style="padding: 10px 30px 30px 30px; border:0; background-color: #f2f0ef; border-spacing: 10px; width: 80%; margin: auto; margin-top: 5%;">
                <tr>
                    <th>
                        <h2 style="text-align: left;">RESTABLECER CONTRASEÑA</h2>
                        <hr style=" background-color: #202020;">
                    </th>
                </tr>
                <tr>
                    <td>
                        <p>
                            Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Eclipse Solutions. 
                            Si fuiste tú quien la solicitó, por favor haz clic en el siguiente enlace para continuar con el proceso:
                        </p>
                        
                        
                            
                        <p>
                            Por seguridad, te recomendamos que al crear una nueva contraseña utilices al menos ocho caracteres, combinando letras mayúsculas y minúsculas, 
                            números y símbolos especiales. Evita usar información personal o contraseñas comunes como “123456” o “password”, y trata de no reutilizar contraseñas 
                            que hayas usado en otros sitios. Si tú no realizaste esta solicitud, puedes ignorar este mensaje. 
                            Tu contraseña actual seguirá siendo válida y no se realizará ningún cambio en tu cuenta.
                        </p>
                        <a href="{link}" style="margin: auto;">
                            <button style="margin: auto; background-color: #202020; color: white; border: none; padding: 1em; font-weight: 700;">
                                RESTABLECER CONTRASEÑA
                            </button>
                        </a>
                        <br>
                    </td>
                </tr>
            </table>
            
                <table role="presentation" style="margin:auto">
                    <tr>
                        <td>
                            <p style="text-align: center;">Gracias, <strong>Eclipse Solutions</strong></p>
                            
                        </td>
                    </tr>
                </table>
            
            <table role="presentation" width="100%" style="margin-top: 40px;">
                <tr>
                    <td>
                        <img src="cid:logo_eclipse" alt="Logo" width="100" height="80" style="display: block;">
                    </td>
                </tr>
            </table>
        </div>
        
    </body>
</html>
    """

    conexion = get_connection(
        host='smtp.gmail.com',
        port=465,
        username=sender,
        password=sender_pass,
        use_ssl=True
    )

    mensaje = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=sender,
        to=[receiver],
        connection=conexion,
    )

    mensaje.attach_alternative(html_body,'text/html')

    with open(route_image, "rb") as img:
        mime_img = MIMEImage(img.read())
        mime_img.add_header("Content-ID", "<logo_eclipse>")
        mensaje.attach(mime_img)
    mensaje.send()

    
