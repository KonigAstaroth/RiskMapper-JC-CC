from django.shortcuts import render

def login (request):
    return render(request, 'login.html')

def policy (request):
    return render(request, 'policy.html')

# Create your views here.
