from django.shortcuts import redirect
from app.core.auth.firebase_config import auth

PUBLIC_URLS = ["/","/login/", "/logout/", '/login-process/']

class loginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in PUBLIC_URLS:
            return self.get_response(request)
        
        sessionCookie = request.COOKIES.get('session')

        if not sessionCookie:
            return redirect ("login")
        try:
            auth.verify_session_cookie(sessionCookie, check_revoked=True)
        except:
            return redirect("login")
     
        return self.get_response(request)