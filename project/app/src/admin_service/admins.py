from django.shortcuts import redirect
import urllib
from app.core.auth.firebase_config import db, auth

def getPrivileges(request):
     sessionCookie = request.COOKIES.get('session')
     decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
     uid = decoded_claims["uid"]
     doc_ref = db.collection("Usuarios").document(uid)
     doc = doc_ref.get()
     if doc.exists:
          return doc.to_dict().get("privileges",False)
     else:
          return False
     
def adduser(request):
        priv = getPrivileges(request)
        sessionCookie = request.COOKIES.get('session')

        try:
            decoded_claims = auth.verify_session_cookie(sessionCookie, check_revoked=True)
            uid = decoded_claims["uid"]
        except:
            return redirect("login")

        priv = getPrivileges(request)
        if not priv:
                return redirect("main")

        if not sessionCookie:
            return redirect ("login")

        if request.method == "POST":
            
            email = request.POST.get("email")
            password = request.POST.get("password")
            name = request.POST.get("name")
            lastname = request.POST.get("lastname")
            privileges = request.POST.get('privileges')

        if name and lastname and password and email and privileges:
                
            try:
                user = auth.create_user(email=email, password=password)
                db.collection("Usuarios").document(user.uid).set({
                "email": email,
                "name": name,
                "lastname": lastname,
                "privileges":privileges,
                "lastAccess": None
                
                })
                success_message = "Usuario agregado correctamente"
                return redirect(f"/add?success={urllib.parse.quote(success_message)}")
            except Exception as e:
                error_message = str(e)
                return redirect(f"/add?error={urllib.parse.quote(error_message)}")            
        else:
            error_message = "Faltan campos por ser llenados"
            return redirect(f"/add?error={urllib.parse.quote(error_message)}")
        


def editUser(request, id):
     
     if request.method == 'POST':
        uid = id
        updates = {}

        if name := request.POST.get('name'):
            updates['name'] = name

        if lastname := request.POST.get('lastname'):
            updates['lastname'] = lastname

        if email := request.POST.get('email'):
            updates['email'] = email
            if uid:
                try:
                    auth.update_user(uid, email=email)
                except Exception as e:
                    print("Error actualizando email:", e)

        if password := request.POST.get('password'):
            if uid:
                try:
                    auth.update_user(uid, password=password)
                except Exception as e:
                    print("Error actualizando contraseña:", e)

        if privileges := request.POST.get('privileges'):
            updates['privileges'] = privileges == 'true'

        if updates:
            db.collection('Usuarios').document(id).update(updates)
     return redirect('manageUser')


def deleteUser(request, id):
     if request.method == 'POST':
          doc_ref = db.collection('Usuarios').document(id)
          doc = doc_ref.get()
          if doc.exists:
               uid = id
               doc_ref.delete()
               if uid:
                    try:
                         auth.delete_user(uid)
                    except auth.UserNotFoundError:
                         pass
          
     return redirect('manageUser')