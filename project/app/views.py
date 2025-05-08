import requests
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib import messages
from firebase_admin import firestore, auth
from django.conf import settings
import urllib.parse


db = firestore.client()

FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}"

def login(request):
    if request.method == 'POST':


        recaptcha_response = request.POST.get('g-recaptcha-response')

        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        result = requests.post(verify_url, data=data).json()

        if not result.get('success'):
            messages.error(request, "Se debe de validar el CAPTCHA")
            return redirect('/')
        
        email = request.POST["email"]
        password = request.POST["password"]
        login = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(FIREBASE_AUTH_URL, json=login)

        if response.status_code == 200:
                user_data = response.json()
                request.session["firebase_uid"] = user_data["localId"]
                request.session["email"] = email
                request.session["firebase_token"] = user_data["idToken"]
                return redirect("main")
        else:
             messages.error(request, "Correo o contraseña incorrectos") 
             return redirect('/')
    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

def forgotpass (request):
    return render(request, 'forgotPass.html')

def main (request):
     return render (request, 'main.html')

def add (request):
     
     if request.method == "POST":
          
        email = request.POST["email"]
        password = request.POST["password"]
     
        user = auth.create_user(email=email, password=password)
        db.collection("Usuarios").document(user.uid).set({
            "email": email
        })
        return redirect('login')


     return render (request, "addUser.html")

# Create your views here.
