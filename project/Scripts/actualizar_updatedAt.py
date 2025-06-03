from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from django.conf import settings
from firebase_admin import credentials, firestore
import firebase_admin
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  

cred_path = "C:\\Users\\roboe\\OneDrive\\Documentos\\GitHub\\RiskMapper-JC-CC\\project\\project\\riskmapper-jc-cc-firebase-adminsdk-fbsvc-a6ee255385.json"

cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred)
db = firestore.client()


def agregar_updatedAt_a_eventos():
    ref = db.collection('Eventos')
    docs = ref.stream()

    now = datetime.datetime.now(datetime.timezone.utc)

    for doc in docs:
        doc_ref = ref.document(doc.id)
        doc_ref.update({
            'updatedAt': now
        })
        print(f'Documento {doc.id} actualizado con updatedAt={now}')

if __name__ == "__main__":
    agregar_updatedAt_a_eventos()