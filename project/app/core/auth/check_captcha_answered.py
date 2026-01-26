import requests
from django.conf import settings

def checkCaptcha(recaptcha_response):
    data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    result = requests.post(verify_url, data=data).json()

    return result