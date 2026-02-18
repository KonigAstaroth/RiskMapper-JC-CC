import pdfplumber
import io
import requests

def contextEnsu(municipio):
    url = 'https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/ensu/ENSU2026_01_RR.pdf'
    response = requests.get(url)
    extract = ""

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:

        table = pdf.pages[6].extract_table()
        row_municipio = [row for row in table if row and municipio in str(row)]
        extract = str(row_municipio)
        if extract:
            return f"Basado en este texto: {extract}, ¿Cuál es el porcentaje de inseguridad en {municipio} en diciembre 2025? Unicamente toma en cuenta {municipio}, ningun otro mencionado en la tabla"
        else:
            return "Porcentaje de inseguridad no encontrado"
