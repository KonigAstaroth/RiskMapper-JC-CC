import re

def cleanAnswer(texto):
    texto = texto.strip()
    texto = re.sub(r'\n?[^.\n]*\?$', '', texto).strip()

    patrones_finales = [
        r'Si desea.*?$',
        r'¿Desea.*?$',
        r'¿Le gustaría.*?$',
        r'¿Quiere que.*?$',
    ]
    for patron in patrones_finales:
        texto = re.sub(patron, '', texto, flags=re.IGNORECASE).strip()

    
    texto = re.sub(r'^#{1,6}\s*(.*)', r'<h3>\1</h3>', texto, flags=re.MULTILINE)

    
    texto = re.sub(r'^[\-\*]\s+(.*)', r'<li>\1</li>', texto, flags=re.MULTILINE)
    if '<li>' in texto:
        texto = '<ul>' + texto + '</ul>'

    texto = re.sub(r'^\d+\.\s+(.*)', r'<li>\1</li>', texto, flags=re.MULTILINE)
    if re.search(r'<li>.*</li>', texto) and not texto.startswith('<ul>'):
        texto = '<ol>' + texto + '</ol>'

    # Negritas y cursivas
    texto = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', texto)
    texto = re.sub(r'\*(.*?)\*', r'<em>\1</em>', texto)

    
    def procesar_tabla(match):
        tabla = match.group(0)
        filas = tabla.strip().split('\n')
        if len(filas) < 2:
            return tabla

        cabecera = filas[0]
        cuerpo = filas[2:] if re.match(r'^\|[-\s|]+\|$', filas[1]) else filas[1:]

        def fila_a_html(fila, tag='td'):
            celdas = [f'<{tag} style="border: 1px solid #000; padding: 5px;">{c.strip()}</{tag}>' for c in fila.strip('|').split('|')]
            return '<tr>' + ''.join(celdas) + '</tr>'

        tabla_html = '<table style="border-collapse: collapse; width: 100%;">'
        tabla_html += fila_a_html(cabecera, tag='th')
        for fila in cuerpo:
            if fila.strip():
                tabla_html += fila_a_html(fila)
        tabla_html += '</table>'

        return tabla_html

    
    texto = re.sub(
        r'((?:\|.*\|\n)+\|[-\s|]+\|\n(?:\|.*\|\n?)*)',
        procesar_tabla,
        texto,
        flags=re.MULTILINE
    )

    
    bloques = texto.split('\n\n')
    html_parts = []
    for b in bloques:
        b = b.strip()
        if not b:
            continue
        if '<table' in b:
            html_parts.append(b)
        else:
            html_parts.append(f'<p>{b}</p>')

    return ''.join(html_parts)