from django.shortcuts import redirect
from app.core.auth.firebase_config import auth

PUBLIC_URLS = ["/", "/logout/", '/login-process/']

class loginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in PUBLIC_URLS:
            return self.get_response(request)
        
        sessionCookie = request.COOKIES.get('session')
        if not sessionCookie:
            return redirect("login")

        if not any(request.path.startswith(url) for url in PUBLIC_URLS) and sessionCookie is None:
            try:
                decoded = auth.verify_session_cookie(sessionCookie, check_revoked=True)
                request.uid = decoded["uid"]
                return self.get_response(request)  
            except:
                response = redirect('login')
                response.delete_cookie('session')
                return response
     
        return self.get_response(request)