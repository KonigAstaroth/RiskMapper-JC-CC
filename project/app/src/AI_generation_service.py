import os
from openai import OpenAI
from django.conf import settings
from app.src.utils.clean_answer_helper import cleanAnswer
     
def loadOsintDate(name = "osintDate.txt" ):
     ruta = os.path.join(settings.BASE_DIR, 'app','prompts', name)
     with open (ruta, 'r', encoding='utf-8')as f:
          return f.read()

def genAI(filters,start,end, descripcion_cliente,now, request):
     client = OpenAI(api_key=settings.OPENAI_API_KEY)
     lugar = ', '.join(f"{k}:{v}" for k,v in filters.items()) if filters else "No especificado"
     template = loadOsintDate()
     content= template.format(start=start, end = end, lugar = lugar, descripcion_cliente = descripcion_cliente, now = now, lang = request.session.get('lang'))
     completion =client.chat.completions.create(
          model='gpt-4.1-mini',
          store = True,
          messages=[{'role': 'user', 'content': content}]
     )

     
     text = completion.choices[0].message.content.strip()
     
     return cleanAnswer(text)