ICON_MAP = {
    "amenazas": "amenazas",
    "robo a negocio": "robonegocio",
    "homicidio doloso": "homicidiodoloso",
    "feminicidio": "feminicidio",
    "secuestro": "secuestro",
    "trata de personas": "tratapersonas",
    "robo a transeúnte": "robotranseunte",
    "extorsión": "extorsion",
    "robo a casa habitación": "robocasa",
    "violación": "violacion",
    "narcomenudeo": "narcomenudeo",
    "arma de fuego": "armafuego",
    "robo de vehículo": "robovehiculo",
    "robo de accesorios de auto": "robovehiculo",
    "robo a cuentahabiente": "robocuentahabiente",
    "robo a pasajero a bordo de microbus": "robomicrobus",
    "robo a repartidor": "roborepartidor",
    "robo a pasajero a bordo del metro": "robometro",
    "robo a pasajero a bordo de taxi": "robotaxi",
    "robo a transportista": "robotransportista",
    "hecho no delictivo": "nodelito",
    "bajo impacto": "bajoimpacto"
}


def resolveIcons(text:str) -> str:
    if not isinstance(text, str):
        return "default"
    text = text.lower()
    for key, icon in ICON_MAP.items():
        if key in text:
            return icon
    return "default"