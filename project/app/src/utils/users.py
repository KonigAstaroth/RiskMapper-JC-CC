from app.core.auth.firebase_config import db

def getUsers():
     docs = db.collection("Usuarios").stream()
     listUsers=[]

     for doc in docs:
          datos = doc.to_dict()
          datos['id'] = doc.id
          listUsers.append(datos)

     return listUsers