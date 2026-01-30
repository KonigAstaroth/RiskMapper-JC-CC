import datetime
import pandas as pd


def resolveDate(fecha):
    if isinstance(fecha, pd.Timestamp):
            return fecha.to_pydatetime()
    if isinstance(fecha, datetime.datetime):
            return fecha
    if isinstance(fecha, str):
            fecha = fecha.strip()
            formatos_validos = [
                "%d/%m/%Y",    
                "%Y-%m-%d",      
                "%-d/%-m/%Y",    
                "%#d/%#m/%Y"     
            ]
            for fmt in formatos_validos:
                try:
                    return datetime.datetime.strptime(fecha, fmt)
                except:
                    continue
    return None

def resolveTime(h):
    if isinstance(h, str):
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.datetime.strptime(h, fmt).time()
                except:
                    continue
    if isinstance(h, datetime.time):
            return h
    if isinstance(h, datetime.datetime):
            return h.time()
    return None

def combineDateTime(fecha, hora):
    if isinstance(fecha, datetime.datetime) and isinstance(hora, datetime.time):
        return datetime.datetime.combine(fecha.date(), hora)
    return None