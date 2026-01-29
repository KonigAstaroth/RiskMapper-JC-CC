from django.shortcuts import redirect


def logout (request):
     response = redirect("login")
     response.delete_cookie('session')
     request.session.flush()
     
     return response