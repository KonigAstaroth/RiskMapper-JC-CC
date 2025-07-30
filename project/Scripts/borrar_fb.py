import firebase_admin
from firebase_admin import credentials, firestore
import os
from django.core.cache import cache
import django

CACHE_KEY_MARKERS = 'firebase_markers'
CACHE_KEY_LAST_UPDATE = 'firebase_markers_last_update'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred_path = os.path.join(BASE_DIR, 'riskmapper-jc-cc-firebase-adminsdk-fbsvc-a6ee255385.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')  # Reemplaza por el nombre de tu proyecto Django
# django.setup()

# 2. Inicializa el cliente de Firestore
db = firestore.client()

# 3. Configura los parámetros del filtro
coleccion = "Eventos"         
campo_filtro = "Estado_hechos"                
valor_a_borrar = "Colima"           

# 4. Obtener y borrar documentos que coincidan
docs = db.collection(coleccion).where(campo_filtro, "==", valor_a_borrar).stream()

contador = 0
for doc in docs:
    print(f"Borrando documento ID: {doc.id}")
    db.collection(coleccion).document(doc.id).delete()
    contador += 1

# cache.delete(CACHE_KEY_LAST_UPDATE)
# cache.delete(CACHE_KEY_MARKERS)

print(f"✅ Total de documentos eliminados: {contador}")