# auth.py

# Simulación de repositorio de usuarios de CP
USUARIOS_DB = {
    "asesor1": {"pwd": "123", "rol": "Asesor Comercial", "nombre": "Carlos (Asesor)"},
    "asesor2": {"pwd": "123", "rol": "Asesor Comercial", "nombre": "Ana (Asesora)"},
    "contabilidad": {"pwd": "123", "rol": "Contabilidad", "nombre": "Mariela (Conta)"},
    "comercial": {"pwd": "123", "rol": "Dirección Comercial", "nombre": "Luis (Comercial)"},
    "produccion": {"pwd": "123", "rol": "Producción", "nombre": "Equipo Producción"},
    "fabrica1": {"pwd": "123", "rol": "Fábrica", "nombre": "Planta Fábrica"},
    "facturacion1": {"pwd": "123", "rol": "Facturación", "nombre": "Área Facturación"}
}

def autenticar_usuario(usuario, contrasena):
    """Valida las credenciales y retorna los datos del usuario si son correctos."""
    usuario_key = usuario.lower()
    if usuario_key in USUARIOS_DB and USUARIOS_DB[usuario_key]["pwd"] == contrasena:
        return {"usuario": usuario_key, "rol": USUARIOS_DB[usuario_key]["rol"], "nombre": USUARIOS_DB[usuario_key]["nombre"]}
    return None