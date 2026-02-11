from app.core.auth.firebase_config import db

def getUsers(query=None):
     docs = db.collection("Usuarios").stream()
     listUsers=[]

     for doc in docs:
          datos = doc.to_dict()
          datos['id'] = doc.id
          if query:
            if (query.lower() in datos.get("email", "").lower() or
                query.lower() in datos.get("name", "").lower() or
                query.lower() in datos.get("lastname", "").lower()):
                listUsers.append(datos)
          else:
               listUsers.append(datos)
              

     return listUsers