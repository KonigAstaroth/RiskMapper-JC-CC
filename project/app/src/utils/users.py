from app.core.auth.firebase_config import db
from google.cloud.firestore_v1.base_query import FieldFilter

def getUsers(query=None, role_filter = None):
     ref = db.collection("Usuarios")

     if role_filter and role_filter != 'All':
          if role_filter == "True":
               query_ref = ref.where(filter=FieldFilter("privileges", "==", True))
          elif role_filter == "False":
               query_ref = ref.where("privileges", "==", False)
     else: 
          query_ref = ref 
     
     docs = query_ref.stream()
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