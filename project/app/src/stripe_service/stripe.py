from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from app.core.auth.firebase_config import auth, db
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_user(request):
     email = request.session.get('email_usr')
     plan = request.session.get('plan')
     customer= None

     if not email or not plan:
          return HttpResponse("Faltan datos en la sesión", status=400)
     
     try:
          
          user = auth.get_user_by_email(email)
     except:
          return HttpResponse('Usuario no autenticado', status=401)


     user_doc = db.collection('Usuarios').document(user.uid)
     user_data = user_doc.get().to_dict()

     customer_id = user_data.get('stripe_customer_id')

     if not 'stripe_customer_id' in user_data:
          customer = stripe.Customer.create(
               email= user_data.get('email'),
               name= user_data.get('name') + " " + user_data.get('lastname')
          )
          customer_id = customer.id
          user_doc.update({'stripe_customer_id': customer_id})


     
     prices = {
          'esencial': 'price_1RnkWOPF5qcM1JsRRk5zLJlj',
          'premium': 'price_1RnkZ2PF5qcM1JsRiwtjRrw4',
          'profesional': 'price_1RnkbEPF5qcM1JsRSjBsHD9l'
     }

     if plan not in prices:
        return HttpResponse("Plan inválido", status=400)

     checkout_session = stripe.checkout.Session.create(
          customer= customer_id,
          payment_method_types=['card'],
          line_items=[{
               'price': prices[plan],
               'quantity': 1
          }],
          mode= 'subscription',
          success_url='http://127.0.0.1:8000/success?session_id={CHECKOUT_SESSION_ID}',
          cancel_url='http://127.0.0.1:8000/cancel',
          metadata={
                'firebase_uid': user.uid,
                'plan': plan
          }

     )
     return redirect(checkout_session.url)

def processSubscription(request):
     # if  not all( k in request.session for k in ['name_usr', 'lastname_usr', 'email_usr', 'password_usr', 'client_usr' ]):
     #      return redirect('signup')
     if request.method == "POST":
        plan = request.POST.get('plan')
        request.session['plan'] = plan
        return create_stripe_user(request)