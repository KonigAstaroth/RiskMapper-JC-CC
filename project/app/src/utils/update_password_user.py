from app.core.auth.firebase_config import auth
from django.shortcuts import redirect
from app.src.logout import logout
import urllib.parse


def updateUserPassword(request):
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    sym = ['^', '$', '*', '.', '[', ']', '{', '}', '(', ')', '?', '!', '@', '#', '%', '&', '/', '_', '~', '-']
    has_digit = has_upper = has_lower = has_sym = False
    if request.method == 'POST':
        new_password = request.POST.get('password')
        c_password = request.POST.get('c_password')

        if new_password != c_password:
            error_message = "Las contraseñas no coinciden"
            return redirect(f"/settings?error={urllib.parse.quote(error_message)}")
        
        if len(new_password) < 8:
            error_message = "Mínimo 8 caracteres"
            return redirect(f"/settings?error={urllib.parse.quote(error_message)}")
        if len(new_password) > 30:
            error_message = "Máximo 30 caracteres"
            return redirect(f"/settings?error={urllib.parse.quote(error_message)}")
        
        if any(char.isdigit() for char in new_password):
            has_digit = True
    
        if any(char.isupper() for char in new_password):
            has_upper = True

        if any(char.islower() for char in new_password):
            has_lower = True

        if any(char in sym for char in new_password):
            has_sym = True

        if has_sym and has_digit and has_lower and has_upper:
            try:
                auth.update_user(uid, password = new_password)
                return logout(request)
            except:
               error_message = "Usuario no encontrado"
               return redirect(f"/settings?error={urllib.parse.quote(error_message)}") 
        else:
            error_message = "La contraseña no cumple con las reglas"
            return redirect(f"/settings?error={urllib.parse.quote(error_message)}") 