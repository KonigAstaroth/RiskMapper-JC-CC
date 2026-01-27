import base64
from docx.shared import Inches, Pt
from bs4 import BeautifulSoup
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.http import HttpResponse
from docx import Document
import datetime
from datetime import timezone
from io import BytesIO


def ProcessDocx(request):
     graphic = request.session.get('graphic')
     calendarios = request.session.get('calendarios', [])
     horas = request.session.get('hour_txt')
     AiText = request.session.get('AiText')
     lang = request.session.get('lang')
     text_html = AiText
     tabla_img = request.session.get('tabla_base64')

     doc = Document()
     if lang == 'en':
          doc.add_heading('Event analysis', 0)
     elif lang == 'es':
          doc.add_heading('Análisis de eventos', 0)
     if text_html:
        soup = BeautifulSoup(text_html, 'html.parser')
        for elemento in soup.contents:
            if elemento.name == 'p':
                doc.add_paragraph(elemento.get_text())
            elif elemento.name == 'h3':
                doc.add_heading(elemento.get_text(), level=2)
            elif elemento.name == 'ul':
                for li in elemento.find_all('li'):
                    doc.add_paragraph('• ' + li.get_text(), style='List Bullet')
            elif elemento.name == 'ol':
                for li in elemento.find_all('li'):
                    doc.add_paragraph(li.get_text(), style='List Number')
            elif elemento.name == 'table':
                filas = elemento.find_all('tr')
                if filas:
                    num_cols = len(filas[0].find_all(['td', 'th']))
                    tabla = doc.add_table(rows=1, cols=num_cols)
                    tabla.style = 'Table Grid'

                    # Encabezado
                    hdr_cells = tabla.rows[0].cells
                    for idx, th in enumerate(filas[0].find_all(['td', 'th'])):
                        hdr_cells[idx].text = th.get_text().strip()
                        for paragraph in hdr_cells[idx].paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            for run in paragraph.runs:
                                run.font.bold = True
                                run.font.size = Pt(11)

                    # Cuerpo de la tabla
                    for fila in filas[1:]:
                        celdas = fila.find_all(['td', 'th'])
                        row_cells = tabla.add_row().cells
                        for idx, celda in enumerate(celdas):
                            row_cells[idx].text = celda.get_text().strip()
                            for paragraph in row_cells[idx].paragraphs:
                                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                for run in paragraph.runs:
                                    run.font.size = Pt(10)

                    # Ajustar ancho de columnas (opcional)
                    ancho_columna = Inches(1.5)
                    for col_idx in range(num_cols):
                        for row in tabla.rows:
                            row.cells[col_idx].width = ancho_columna

     for calendario in calendarios:
          img_base64 = calendario.get('img')
          if img_base64:
               if img_base64.startswith('data:image'):
                    img_base64 = img_base64.split(',')[1]
               try:
                    calendario_data = base64.b64decode(img_base64)
                    calendario_stream = BytesIO(calendario_data)
                    if lang == 'en':
                         doc.add_heading('Distribution graphic by date:', level= 2)
                    elif lang == 'es':
                         doc.add_heading('Gráfico de distribución por fecha:', level= 2)
                    doc.add_picture(calendario_stream, width=Inches(3))  
               except:
                    doc.add_paragraph('Error al cargar calendario')

     if graphic :
          for g in graphic:
               img = g.get('img')
               if img.startswith('data:image'):
                    img = img.split(',')[1]
               try:
                    graphic_data = base64.b64decode(img)
                    graphic_stream = BytesIO(graphic_data)
                    if lang == 'en':
                         doc.add_heading('Distribution graphic by time:', level= 2)
                    elif lang == 'es':
                         doc.add_heading('Gráfico de distribución horaria:', level= 2)
                    doc.add_picture(graphic_stream, width=Inches(4))  
               except:
                    doc.add_paragraph('Error al agregar calendario')

     if tabla_img:
          
          try:
               if isinstance(tabla_img, bytes):
                    tabla_img = tabla_img.decode('utf-8')
               tabla_img = tabla_img.strip().replace('\n', '')
               if tabla_img.startswith('data:image'):
                    tabla_img = tabla_img.split(',')[1]

               # Decodificar
               tabla_data = base64.b64decode(tabla_img)
               tabla_stream = BytesIO(tabla_data)
               if lang == 'en':
                    doc.add_heading('Data table:', level= 2)
               elif lang == 'es':
                    doc.add_heading('Tabla de datos:', level= 2)
               doc.add_picture(tabla_stream, width=Inches(3))
          except:
               doc.add_paragraph('Error en la tabla de datos')
     if horas:
          try:
               if lang == 'en':
                    doc.add_heading('Critic time range:', level= 2)
               elif lang == 'es':
                    doc.add_heading('Rango horario crítico:', level= 2)
               doc.add_paragraph( horas)
          except:
               doc.add_paragraph("No hay rango horario crítico")
     

     response = HttpResponse(
          content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
     )

     fechaHora = datetime.datetime.now(timezone.utc)

     response['Content-Disposition'] = f'attachment; filename =Analisis_de_eventos{fechaHora}.docx'
     doc.save(response)
     request.session.pop('graphic', None)
     request.session.pop('calendarios', None)
     request.session.pop('hour_txt', None)
     request.session.pop('AiText', None)
     request.session.pop('ready_to_export', None)
     request.session.pop('tabla_base64', None)

     return response