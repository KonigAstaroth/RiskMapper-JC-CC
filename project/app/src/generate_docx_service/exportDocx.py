import base64
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from bs4 import BeautifulSoup
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

def add_horizontal_line(doc, length_in_inches, align):
    p = doc.add_paragraph()
    p_format = p.paragraph_format
    p_format.space_before = 0
    p_format.space_after = 0

    # Si se define longitud, centramos la línea ajustando márgenes
    if length_in_inches is not None:
        total_width = 6.0  # ancho estimado del cuerpo de texto en pulgadas
        margin = max((total_width - length_in_inches) / 2, 0)
        p_format.left_indent = Inches(margin)
        p_format.right_indent = Inches(margin)
        if align == "center":
            margin = max((total_width - length_in_inches) / 2, 0)
            p_format.left_indent = Inches(margin)
            p_format.right_indent = Inches(margin)
        elif align == "right":
            p_format.left_indent = Inches(total_width - length_in_inches)
            p_format.right_indent = Inches(0)
        elif align == "left":
            p_format.left_indent = Inches(0)
            p_format.right_indent = Inches(total_width - length_in_inches)

    p_element = p._p
    pPr = p_element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')  # grosor
    bottom.set(qn('w:space'), '1')          # separación con texto
    bottom.set(qn('w:color'), '000000')        # color
    pBdr.append(bottom)
    pPr.append(pBdr)


def ProcessDocx(request):
     graphic = request.session.get('graphic')
     calendarios = request.session.get('calendarios', [])
     horas = request.session.get('hour_txt')
     AiText = request.session.get('AiText')
     lang = request.session.get('lang')
     now_str = request.session.get('now_str')
     place_str = request.session.get('place_str')
     text_html = AiText
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
     if text_html:
        soup = BeautifulSoup(text_html, 'html.parser')
        for elemento in soup.contents:
            if elemento.name == 'p':
                doc.add_paragraph(elemento.get_text())
            elif elemento.name == 'h2':
               doc.add_heading(elemento.get_text(), level=1)
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

     response['Content-Disposition'] = f'attachment; filename =Analisis_de_eventos{fechaHora}.docx'
     doc.save(response)
     request.session.pop('graphic', None)
     request.session.pop('calendarios', None)
     request.session.pop('hour_txt', None)
     request.session.pop('AiText', None)
     request.session.pop('ready_to_export', None)
     request.session.pop('tabla_base64', None)
     request.session.pop('now_str', None)
     request.session.pop('place_str', None)

     return response