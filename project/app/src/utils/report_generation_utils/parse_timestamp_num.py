def time_to_num(time_str):
     try:
          hh, mm, ss = map(int, time_str.strip().split(':'))
          return ss +60*(mm + 60*hh)
     except Exception as e:
          print(f"Error al convertir '{time_str}': {e}")
          return None