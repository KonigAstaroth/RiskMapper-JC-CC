import os
from openai import OpenAI
from django.conf import settings
from app.src.utils.clean_answer_helper import cleanAnswer
from app.src.you_search_service import YouWebSearch
from app.src.utils.ensu_service import contextEnsu
     
def loadOsintDate():
     ruta = os.path.join(settings.BASE_DIR, 'app','prompts', "osint.txt")
     with open (ruta, 'r', encoding='utf-8')as f:
          return f.read()

def genAI(filters,start,end, now, crimes_select, request, eventos_db):
     client = OpenAI(api_key=settings.OPENAI_API_KEY)

     results = YouWebSearch(start, end, filters, crimes_select)
     municipio = filters.get('Municipio')
     ensu_text = contextEnsu(municipio)

     lugar = ', '.join(f"{k}: {v}" for k,v in filters.items()) if filters else "No especificado"
     request.session['place_str'] = lugar
     template = loadOsintDate()

     content= template.format(
          start=start, end = end, lugar = lugar, 
          now = now, lang = request.session.get('lang'), results = results,
          ensu_text = ensu_text, eventos_db = eventos_db
     )

     completion =client.chat.completions.create(
          model='gpt-4.1-mini',
          store = True,
          messages=[{'role': 'user', 'content': content}]
     )

     
     text = completion.choices[0].message.content.strip()
     request.session['AI_text_markdown'] = text
     
     return cleanAnswer(text)