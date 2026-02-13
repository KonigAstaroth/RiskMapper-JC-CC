import os
from openai import OpenAI
from django.conf import settings
from app.src.utils.clean_answer_helper import cleanAnswer
from app.src.you_search_service import YouWebSearch

# TODO: Pass YouWebSearch results to genAI context
# TODO: Change prompt to accept YouWebSearch results
     
def loadOsintDate():
     ruta = os.path.join(settings.BASE_DIR, 'app','prompts', "Osint.txt")
     with open (ruta, 'r', encoding='utf-8')as f:
          return f.read()

def genAI(filters,start,end, now, crimes_select, request):
     client = OpenAI(api_key=settings.OPENAI_API_KEY)

     results = YouWebSearch(start, end, filters, crimes_select)

     lugar = ', '.join(f"{k}: {v}" for k,v in filters.items()) if filters else "No especificado"
     request.session['place_str'] = lugar
     template = loadOsintDate()

     content= template.format(
          start=start, end = end, lugar = lugar, 
          now = now, lang = request.session.get('lang'), results = results
     )

     completion =client.chat.completions.create(
          model='gpt-4.1-mini',
          store = True,
          messages=[{'role': 'user', 'content': content}]
     )

     
     text = completion.choices[0].message.content.strip()
     
     return cleanAnswer(text)