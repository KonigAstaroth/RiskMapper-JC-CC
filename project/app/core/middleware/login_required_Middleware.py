from django.shortcuts import redirect
from app.core.auth.firebase_config import auth

PUBLIC_URLS = ["/", "/logout/", '/login-process/', '/forgotPassword/', '/forgotPassword-sendMail/', '/recoverPass/']

class loginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)
        
        if path in PUBLIC_URLS:
            return self.get_response(request)
        
        sessionCookie = request.COOKIES.get('session')
        if not sessionCookie:
            return redirect("login")
        
        try:
            decoded = auth.verify_session_cookie(sessionCookie, check_revoked=True)
            request.uid = decoded["uid"]
            return self.get_response(request)  
        except Exception as e:
            response = redirect('login')
            response.delete_cookie('session')
            return response