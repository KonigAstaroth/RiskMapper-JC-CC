from django.shortcuts import redirect


def logout (request):
     request.session.flush()
     response = redirect("login")
     response.delete_cookie('session')
     
     return response