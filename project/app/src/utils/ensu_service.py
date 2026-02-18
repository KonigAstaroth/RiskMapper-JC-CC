import pdfplumber
import io
import requests

def contextEnsu(municipio):
    url = 'https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/ensu/ENSU2026_01_RR.pdf'
    response = requests.get(url)
    reduced_context =''

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if municipio in text:
                reduced_context += text
                return f"Basado en este texto: {reduced_context}, ¿Cuál es el porcentaje de inseguridad en {municipio} en diciembre 2025?"
            else:
                return "Porcentaje de inseguridad no encontrado"
