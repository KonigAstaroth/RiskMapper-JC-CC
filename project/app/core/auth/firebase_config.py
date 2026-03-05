import firebase_admin
import os
from firebase_admin import credentials, firestore, auth #en la config de storage cambiar las reglas a modo de produccion 
from django.conf import settings
from decouple import config
import json

FIREBASE_API_KEY= config('FIREBASE_API_KEY', default=None)
# firebase_json_str = os.environ.get("FIREBASE_JSON")


# DEBUGGING
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# cred_path = os.path.join(BASE_DIR, 'etc','secrets','riskmapper-jc-cc-firebase-adminsdk-fbsvc-a6ee255385.json')

#Production
cred_path = '/etc/secrets/riskmapper-jc-cc-firebase-adminsdk-fbsvc-a6ee255385.json'
cred = credentials.Certificate(cred_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}"

db = firestore.client()

firebase_auth = auth