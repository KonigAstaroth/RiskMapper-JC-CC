import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import base64
import gc
import numpy as np
import calendar


def genDataImg(cat_color_cuenta):
     n = len(cat_color_cuenta)
     radio = 0.4                  
     espacio = radio * 5          

     alto_total = n * espacio  

     alto_fig = max(alto_total * 0.4, 1)
     fig, ax = plt.subplots(figsize=(6, alto_fig * 0.4))  
     ax.set_aspect('equal')
     ax.axis('off')

     for i, item in enumerate(cat_color_cuenta):
        nombre = item['nombre']
        color = item['color']
        y = (n - i - 1) * espacio

        
        icon = mpatches.Circle((0.5, y), radio, color=color)
        ax.add_patch(icon)

        
        cuenta = item.get('cuenta', 0)
        texto = f"{nombre.upper()}: {cuenta}"
        ax.text(1.2, y, texto, va='center', fontsize=12)

    
     ax.set_xlim(-0.2, 5)
     ax.set_ylim(-radio - 0.5, alto_total - espacio + radio + 0.2)

     plt.tight_layout(pad=0.5)

     buffer = io.BytesIO()
     plt.savefig(buffer, format='png', bbox_inches = 'tight')
     plt.close(fig)
     ax.clear()
     buffer.seek(0)
     img_png = buffer.getvalue()
     tabla = base64.b64encode(img_png).decode('utf-8')
     buffer.close()
     del fig, ax, buffer, img_png
     gc.collect()

     return tabla

def genGraph(puntos):
          if not puntos:
               return None
          
          colores_cat ={
          'DELITO DE BAJO IMPACTO': '#A0A0A0',  # gris
          'ROBO A CUENTAHABIENTE SALIENDO DEL CAJERO CON VIOLENCIA': '#FF0000',  # rojo
          'ROBO DE VEHÍCULO CON Y SIN VIOLENCIA': '#FFA500',  # naranja
          'VIOLACIÓN': '#8B0000',  # rojo oscuro
          'ROBO A PASAJERO A BORDO DE MICROBUS CON Y SIN VIOLENCIA': '#FFD700',  # dorado
          'ROBO A REPARTIDOR CON Y SIN VIOLENCIA': '#ADFF2F',  # verde lima
          'ROBO A PASAJERO A BORDO DEL METRO CON Y SIN VIOLENCIA': '#00FFFF',  # cian
          'LESIONES DOLOSAS POR DISPARO DE ARMA DE FUEGO': '#00008B',  # azul oscuro
          'ROBO A NEGOCIO CON VIOLENCIA': '#FF69B4',  # rosa fuerte
          'HECHO NO DELICTIVO': '#D3D3D3',  # gris claro
          'ROBO A TRANSEUNTE EN VÍA PÚBLICA CON Y SIN VIOLENCIA': '#00FF00',  # verde
          'ROBO A PASAJERO A BORDO DE TAXI CON VIOLENCIA': '#40E0D0',  # turquesa
          'HOMICIDIO DOLOSO': '#4B0082',  # índigo
          'ROBO A CASA HABITACIÓN CON VIOLENCIA': '#800080',  # morado
          'SECUESTRO': '#FF1493',  # rosa mexicano
          'ROBO A TRANSPORTISTA CON Y SIN VIOLENCIA': '#0000FF',
          'AMENAZAS': '#8A2BE2',  # azul violeta
          'ROBO A NEGOCIO': '#FF69B4',  # misma que "ROBO A NEGOCIO CON VIOLENCIA"
          'FEMINICIDIO': '#DC143C',  # carmesí
          'SECUUESTRO': '#FF1493',  # igual que "SECUESTRO"
          'TRATA DE PERSONAS': '#B22222',  # rojo fuego
          'ROBO A TRANSEÚNTE': '#00FF00',  # igual que transeúnte con violencia
          'EXTORSIÓN': '#DAA520',  # dorado oscuro
          'ROBO A CASA HABITACIÓN': '#800080',  # igual que "CON VIOLENCIA"
          'NARCOMENUDEO': '#006400',  # verde oscuro
          'ARMA DE FUEGO': '#00008B',  # igual que lesiones por arma
          'ROBO DE ACCESORIOS DE AUTO': '#A0522D',  # marrón
          'ROBO A PASAJERO A BORDO DE MICROBUS': '#FFD700',  # igual que con violencia
          'ROBO A REPARTIDOR': '#ADFF2F',  # igual que con violencia
          'ROBO A PASAJERO A BORDO DEL METRO': '#00FFFF',  # igual que con violencia
          'ROBO A TRANSPORTISTA': '#0000FF',
          }

          angulos =[]
          radios =[]
          colores = []

          for angulo, radio, categoria in puntos:
               angulos.append(angulo)
               radios.append(radio)
               colores.append(colores_cat.get(categoria, 'gray'))

          fig =  plt.figure(figsize=(6,6))
          ax = plt.subplot(111, polar=True)
          sc = ax.scatter(angulos, radios, color=colores, s=80, alpha=0.75)
          ax.set_theta_direction(-1)
          ax.set_theta_offset(np.pi/2)

          horas =[f"{h:02d}:00" for h in range(24)]
          ticks = [(h/24) * 2 * np.pi for h in range(24)]
          ax.set_xticks(ticks)
          ax.set_xticklabels(horas, fontsize=8)
          ax.set_rlabel_position(135) 
          ax.set_ylim(0,31)
          
          
          buffer = io.BytesIO()
          plt.savefig(buffer, format='png')
          buffer.seek(0)
          img_png = buffer.getvalue()
          graphic = base64.b64encode(img_png).decode('utf-8')
          plt.close(fig)
          ax.clear()
          buffer.close()
          del fig, ax, buffer, img_png
          gc.collect()
          return graphic

def generateCalendar( year: int, month: int, eventos: list[tuple]) -> str:
     cal = calendar.monthcalendar(year, month)
     fig, ax = plt.subplots(figsize=(5,5))
     ax.set_axis_off()
     ax.set_title(calendar.month_name[month] + f" {year}", fontsize=20)

     dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

     colores_cat ={
          'DELITO DE BAJO IMPACTO': '#A0A0A0',  # gris
          'ROBO A CUENTAHABIENTE SALIENDO DEL CAJERO CON VIOLENCIA': '#FF0000',  # rojo
          'ROBO DE VEHÍCULO CON Y SIN VIOLENCIA': '#FFA500',  # naranja
          'VIOLACIÓN': '#8B0000',  # rojo oscuro
          'ROBO A PASAJERO A BORDO DE MICROBUS CON Y SIN VIOLENCIA': '#FFD700',  # dorado
          'ROBO A REPARTIDOR CON Y SIN VIOLENCIA': '#ADFF2F',  # verde lima
          'ROBO A PASAJERO A BORDO DEL METRO CON Y SIN VIOLENCIA': '#00FFFF',  # cian
          'LESIONES DOLOSAS POR DISPARO DE ARMA DE FUEGO': '#00008B',  # azul oscuro
          'ROBO A NEGOCIO CON VIOLENCIA': '#FF69B4',  # rosa fuerte
          'HECHO NO DELICTIVO': '#D3D3D3',  # gris claro
          'ROBO A TRANSEUNTE EN VÍA PÚBLICA CON Y SIN VIOLENCIA': '#00FF00',  # verde
          'ROBO A PASAJERO A BORDO DE TAXI CON VIOLENCIA': '#40E0D0',  # turquesa
          'HOMICIDIO DOLOSO': '#4B0082',  # índigo
          'ROBO A CASA HABITACIÓN CON VIOLENCIA': '#800080',  # morado
          'SECUESTRO': '#FF1493',  # rosa mexicano
          'ROBO A TRANSPORTISTA CON Y SIN VIOLENCIA': '#0000FF',
          'AMENAZAS': '#8A2BE2',  # azul violeta
          'ROBO A NEGOCIO': '#FF69B4',  # misma que "ROBO A NEGOCIO CON VIOLENCIA"
          'FEMINICIDIO': '#DC143C',  # carmesí
          'SECUUESTRO': '#FF1493',  # igual que "SECUESTRO"
          'TRATA DE PERSONAS': '#B22222',  # rojo fuego
          'ROBO A TRANSEÚNTE': '#00FF00',  # igual que transeúnte con violencia
          'EXTORSIÓN': '#DAA520',  # dorado oscuro
          'ROBO A CASA HABITACIÓN': '#800080',  # igual que "CON VIOLENCIA"
          'NARCOMENUDEO': '#006400',  # verde oscuro
          'ARMA DE FUEGO': '#00008B',  # igual que lesiones por arma
          'ROBO DE ACCESORIOS DE AUTO': '#A0522D',  # marrón
          'ROBO A PASAJERO A BORDO DE MICROBUS': '#FFD700',  # igual que con violencia
          'ROBO A REPARTIDOR': '#ADFF2F',  # igual que con violencia
          'ROBO A PASAJERO A BORDO DEL METRO': '#00FFFF',  # igual que con violencia
          'ROBO A TRANSPORTISTA': '#0000FF',
    }

     for i, dias in enumerate(dias_semana):
          ax.text(i+0.5, len(cal), dias, ha='center', va= 'center', fontsize=12, weight='bold')
     

     for fila, semana in enumerate(cal):
          for columna, dia in enumerate(semana):
               if dia != 0:
                    y = len(cal) - fila - 0.5
                    x = columna + 0.5
                    ax.text(x, y + 0.3, str(dia), ha='center', va='top', fontsize=10)
                    for (dia_evento, categoria) in eventos:
                         if dia_evento == dia:
                              color = colores_cat.get(categoria, 'gray')
                              circle = plt.Circle((x, y -0.2), 0.15, color= color)
                              ax.add_patch(circle) 

     plt.xlim(0, 7)
     plt.ylim(0, len(cal) + 1)
     plt.tight_layout()

     buffer = io.BytesIO()
     plt.savefig(buffer, format='png')
     buffer.seek(0)
     imagen_png = buffer.getvalue()
     imagen_base64 = base64.b64encode(imagen_png).decode('utf-8')
     buffer.close()
     
     plt.close()
     return imagen_base64 