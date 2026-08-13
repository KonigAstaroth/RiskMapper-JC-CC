from collections import Counter, defaultdict
import datetime

def getRange(eventos):
    eventos_por_mes = defaultdict(list)

    # Separar eventos por año y mes
    for evento in eventos:
        fecha = evento.get('FechaHoraHecho')
        if not fecha:
            continue

        fecha_dt = None

        if isinstance(fecha, str):
            try:
                fecha_dt = datetime.fromisoformat(fecha)
            except Exception as e:
                print("Error al convertir string a datetime:", e)
                continue

        elif hasattr(fecha, 'to_datetime'):
            try:
                fecha_dt = fecha.to_datetime()
            except Exception as e:
                print("Error al usar to_datetime():", e)
                continue

        elif isinstance(fecha, datetime.datetime):
            fecha_dt = fecha

        else:
            continue

        # (Año, mes) como clave
        clave_mes = (fecha_dt.year, fecha_dt.month)
        eventos_por_mes[clave_mes].append((fecha_dt, evento))

    if not eventos_por_mes:
        return []

    nombres_meses = [
        "enero", "febrero", "marzo", "abril",
        "mayo", "junio", "julio", "agosto",
        "septiembre", "octubre", "noviembre", "diciembre"
    ]

    textos = []

    # Ordenar cronologicamente los meses
    for (anio, mes), eventos_mes in sorted(eventos_por_mes.items()):

        horas = []
        eventos_por_hora = []

        for fecha_dt, evento in eventos_mes:
            hora = fecha_dt.hour
            horas.append(hora)
            eventos_por_hora.append((hora, evento))

        if not horas:
            continue

        # Hora más frecuente del mes
        ctr = Counter(horas)
        hora_critica, cantidad = ctr.most_common(1)[0]

        eventos_criticos = [
            ev for h, ev in eventos_por_hora
            if h == hora_critica
        ]

        # Categoría más frecuente dentro de la hora crítica
        categorias = []

        for ev in eventos_criticos:
            categoria = ev.get('Categoria')

            if categoria:
                categorias.append(categoria.title())

        categoria_critica = None

        if categorias:
            ctr_categorias = Counter(categorias)
            categoria_critica, _ = ctr_categorias.most_common(1)[0]

        nombre_mes = nombres_meses[mes - 1]

        if cantidad > 1:
            texto = (
                f"Durante {nombre_mes} de {anio}, entre las "
                f"{hora_critica}:00 y las {hora_critica + 1}:00 horas "
                f"se registraron {cantidad} eventos. El incidente más "
                f"frecuente en este intervalo fue {categoria_critica}, "
                f"por lo que este rango horario representa un posible "
                f"punto crítico principalmente asociado a este tipo de evento."
            )

        elif cantidad == 1:
            texto = (
                f"Durante {nombre_mes} de {anio}, entre las "
                f"{hora_critica}:00 y las {hora_critica + 1}:00 horas "
                f"se registró 1 evento, lo que destaca este intervalo "
                f"como un posible punto de riesgo. El incidente corresponde "
                f"a {categoria_critica}, lo que indica un posible riesgo "
                f"aislado en este intervalo."
            )

        textos.append(texto)

    return textos