import requests
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib import messages

def login(request):
    if request.method == 'POST':
        recaptcha_response = request.POST.get('g-recaptcha-response')

        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        response = requests.post(verify_url, data=data)
        result = response.json()

        if result.get('success'):
            return redirect('success')
        else:
            messages.error(request, 'reCAPTCHA verification failed. Please try again.')

    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

def forgotpass (request):
    return render(request, 'forgotPass.html')

# Create your views here.
