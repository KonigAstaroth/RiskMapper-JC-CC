import base64
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from django.http import HttpResponse
from docx import Document
import datetime
from datetime import timezone
from io import BytesIO
from app.src.generate_docx_service.parse_markdown_to_docx import markdown_to_docx
from app.src.generate_docx_service.utils import add_horizontal_line



def ProcessDocx(request):
     graphic = request.session.get('graphic')
     calendarios = request.session.get('calendarios', [])
     horas = request.session.get('hour_txt')
     lang = request.session.get('lang')
     now_str = request.session.get('now_str')
     place_str = request.session.get('place_str')
     text_markdown = request.session.get('AI_text_markdown')
     tabla_img = request.session.get('tabla_base64')

     doc = Document()

     # Portada
     doc.add_paragraph("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")  # espacio
     titulo = doc.add_heading("Análisis de Eventos", level=1)
     titulo.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
     subtitulo = doc.add_paragraph(place_str)
     subtitulo.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

     add_horizontal_line(doc, 2.5, 'right')

     fecha = doc.add_paragraph()
     fecha.add_run("Fecha: ").bold = True
     fecha.add_run(str(now_str or ""))
     fecha.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
     

     doc.add_page_break()
     if text_markdown:
        markdown_to_docx(text_markdown, doc)
     doc.add_page_break()

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

     if 'Heading 2' in [s.name for s in doc.styles]:
        style_h2 = doc.styles['Heading 2']
     else:
        style_h2 = doc.styles.add_style('Heading 2', WD_STYLE_TYPE.PARAGRAPH)    

     try:
          style_h1 = doc.styles['Heading 1'] #Estilo de titulo 1

          # Fuente y color
          style_h1.font.size = Pt(24)
          style_h1.font.bold = True
          style_h1.font.color.rgb = RGBColor(0,0,0)

          # Formato del titulo 1
          style_h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
          style_h1.paragraph_format.line_spacing = Pt(30)      
          style_h1.paragraph_format.space_before = Pt(24)      
          style_h1.paragraph_format.space_after = Pt(12) 

          style_h2 = doc.styles['Heading 2'] #Estilo de titulo 2

          #Fuente y color
          style_h2.font.name = 'Calibri'
          style_h2.font.bold = True
          style_h2.font.color.rgb = RGBColor(0,0,0)
          style_h2.font.size = Pt(16)
          style_h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
          style_h2.paragraph_format.space_before = Pt(24)      
          style_h2.paragraph_format.space_after = Pt(12) 

          #Parrafos

          style_p = doc.styles['Normal']  # Estilo de parrafos normales
          # # Fuente y color
          style_p.font.name = 'Calibri'
          style_p.font.size = Pt(11)
          style_p.font.color.rgb = RGBColor(0, 0, 0)

          # # Formato del párrafo
          style_p.paragraph_format.line_spacing = Pt(14)                 
     except Exception:
          pass

     

     response['Content-Disposition'] = f'attachment; filename =Analisis_de_eventos_{now_str}.docx'
     doc.save(response)
     request.session.pop('graphic', None)
     request.session.pop('calendarios', None)
     request.session.pop('hour_txt', None)
     request.session.pop('AiText', None)
     request.session.pop('AI_text_markdown', None)
     request.session.pop('ready_to_export', None)
     request.session.pop('tabla_base64', None)
     request.session.pop('now_str', None)
     request.session.pop('place_str', None)

     return response