import asyncio
import os
from django.shortcuts import redirect
from openai import AsyncOpenAI
from django.conf import settings
import urllib.parse
from app.src.utils.clean_answer_helper import cleanAnswer
from app.src.you_search_service import YouWebSearch
from app.src.utils.ensu_service import contextEnsu
from asgiref.sync import sync_to_async
     
def loadOsintDate():
     ruta = os.path.join(settings.BASE_DIR, 'app','prompts', "Osint.txt")
     with open (ruta, 'r', encoding='utf-8')as f:
          return f.read()

async def genAI(filters, start, end, now, crimes_select, eventos_db, unit_info, prev_start, prev_end):
     try:
          client =AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          municipio = filters.get('Municipio')

          current_search_task = YouWebSearch(start, end, filters, crimes_select)
          ensu_task = sync_to_async(contextEnsu)(municipio)
          template_task = sync_to_async(loadOsintDate)()
          prev_search_task = YouWebSearch(prev_start, prev_end, filters, crimes_select)

          current_results, ensu_text, template, prev_results = await asyncio.gather(
               current_search_task, 
               ensu_task, 
               template_task,
               prev_search_task
          )

          lugar = ', '.join(f"{k}: {v}" for k,v in filters.items()) if filters else "No especificado"

          content= template.format(
               start = start, end = end, lugar = lugar, now = now, current_results = current_results,
               ensu_text = ensu_text, eventos_db = eventos_db, unit_info = unit_info, prev_results = prev_results
          )

          completion = await client.chat.completions.create(
               model='gpt-4.1-mini',
               messages=[{'role': 'user', 'content': content}]
          )

          text = completion.choices[0].message.content.strip()
          
          text_clean = cleanAnswer(text)

          return {
            "ai_text": text_clean,
            "ai_markdown": text,
            "lugar": lugar
          }
     except Exception as e:
          error_message = "Hubo un error al generar el reporte"
          return redirect(f"/main?error={urllib.parse.quote(error_message)}")