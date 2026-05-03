import streamlit as st
import pandas as pd
import base64
import json
import os
from datetime import datetime

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Gestor Documental de Contratos", layout="wide")

# --- BASE DE DATOS LOCAL (JSON) ---
DB_FILE = "base_datos_contratos.json"

def cargar_datos():
    """Lee los contratos desde el archivo JSON local."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_datos(datos):
    """Guarda los contratos en el archivo JSON local."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4)

# --- BASE DE DATOS SIMULADA DE USUARIOS ---
USUARIOS = {
    "asesor1": {"pwd": "123", "rol": "1. Asesor Comercial", "nombre": "Carlos (Asesor)"},
    "asesor2": {"pwd": "123", "rol": "1. Asesor Comercial", "nombre": "Ana (Asesora)"},
    "cumplimiento": {"pwd": "123", "rol": "2. Cumplimiento", "nombre": "Equipo de Cumplimiento"},
    "direccion": {"pwd": "123", "rol": "3. Dirección Comercial", "nombre": "Dirección General"},
    "contabilidad": {"pwd": "123", "rol": "4. Contabilidad", "nombre": "Área Contable"}
}

# --- INICIALIZACIÓN DE ESTADOS DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None

# --- NUEVA FUNCIÓN DE VISUALIZACIÓN SEGURA (OPCIÓN 1) ---
def display_pdf(base64_pdf, nombre_archivo="documento.pdf"):
    """Decodifica el PDF y ofrece un botón de descarga/apertura nativa del navegador"""
    try:
        # Decodificamos el base64 de vuelta a bytes
        bytes_pdf = base64.b64decode(base64_pdf)
        
        st.info("💡 Por políticas de seguridad del navegador, utilice el botón inferior para visualizar o descargar el documento de forma segura.")
        
        # Botón de descarga/visualización nativo
        st.download_button(
            label=f"📥 Abrir / Descargar: {nombre_archivo}",
            data=bytes_pdf,
            file_name=nombre_archivo,
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error("Error al procesar el documento PDF para su visualización.")

# ---------------------------------------------------------
# PANTALLA DE LOGIN
# ---------------------------------------------------------
if not st.session_state.logged_in:
    # Usamos Markdown con HTML para centrar el título principal
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Sistema de Contratos</h1>", unsafe_allow_html=True)
    st.write("") # Añade un pequeño espacio en blanco para que "respire" el diseño
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit_button = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit_button:
                usuario_db = USUARIOS.get(usuario_input.lower())
                if usuario_db and usuario_db["pwd"] == password_input:
                    st.session_state.logged_in = True
                    st.session_state.usuario_actual = usuario_db
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
        
        st.markdown("""
        **Credenciales de prueba:**
        * Asesores: `asesor1`/`asesor2` (Clave: 123)
        * Aprobadores: `cumplimiento`, `direccion`, `contabilidad` (Clave: 123)
        """)

# ---------------------------------------------------------
# APLICACIÓN PRINCIPAL (Usuario Autenticado)
# ---------------------------------------------------------
else:
    usuario_info = st.session_state.usuario_actual
    rol_actual = usuario_info["rol"]
    nombre_actual = usuario_info["nombre"]
    
    # Cargar la base de datos fresca
    contratos_db = cargar_datos()

    # --- BARRA LATERAL ---
    st.sidebar.title("Perfil de Usuario")
    st.sidebar.write(f"**Nombre:** {nombre_actual}")
    st.sidebar.write(f"**Rol:** {rol_actual}")
    st.sidebar.divider()
    
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.usuario_actual = None
        st.rerun()

    st.title(f"🚀 Panel de Trabajo: {rol_actual}")

    # --- ROL 1: ASESOR COMERCIAL ---
    if rol_actual == "1. Asesor Comercial":
        st.header("📄 Registro de Nuevo Contrato")
        
        with st.form("form_carga", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"Registrando a nombre de: **{nombre_actual}**")
                valor_iva = st.number_input("Valor antes de IVA", min_value=0.0)
            with col_b:
                archivo = st.file_uploader("Subir Contrato Firmado (PDF)", type=['pdf'])
            
            enviar = st.form_submit_button("Enviar a Verificación")
            
            if enviar:
                if archivo:
                    base64_pdf = base64.b64encode(archivo.getvalue()).decode('utf-8')
                    nuevo_id = f"CONT-{len(contratos_db) + 1:03d}"
                    
                    nuevo_contrato = {
                        'id': nuevo_id,
                        'asesor': nombre_actual,
                        'valor': valor_iva,
                        'archivo_nombre': archivo.name,
                        'archivo_b64': base64_pdf,
                        'estado': 'En Verificación',
                        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'sagrilaft_req': valor_iva >= 75,
                        'comentarios': ""
                    }
                    contratos_db.append(nuevo_contrato)
                    guardar_datos(contratos_db)
                    st.success(f"Contrato {nuevo_id} cargado y enviado correctamente.")
                else:
                    st.error("Por favor cargue el archivo PDF firmado.")

    # --- LÓGICA COMÚN PARA ROLES DE APROBACIÓN ---
    else:
        estados_por_rol = {
            "2. Cumplimiento": "En Verificación",
            "3. Dirección Comercial": "Pendiente Autorización",
            "4. Contabilidad": "Para Facturar"
        }
        estado_buscado = estados_por_rol.get(rol_actual)
        
        pendientes = [c for c in contratos_db if c['estado'] == estado_buscado]
        
        if not pendientes:
            st.info("No tienes tareas pendientes en tu bandeja de entrada en este momento.")
        else:
            for i, contrato in enumerate(pendientes):
                with st.expander(f"EXPEDIENTE {contrato['id']} - {contrato['asesor']}"):
                    col_info, col_visor = st.columns([1, 1]) # Ajustado para que el visor y datos tengan el mismo ancho
                    
                    with col_info:
                        st.subheader("Datos del Proceso")
                        st.write(f"**Asesor:** {contrato['asesor']}")
                        st.write(f"**Fecha Carga:** {contrato['fecha']}")
                        st.write(f"**Valor:** ${contrato['valor']}")
                        
                        if contrato['sagrilaft_req']:
                            st.warning("⚠️ Requiere Validación SAGRILAFT")
                        
                        idx_real = next((index for (index, d) in enumerate(contratos_db) if d["id"] == contrato["id"]), None)
                        
                        # --- ACCIONES ---
                        if rol_actual == "2. Cumplimiento":
                            coment = st.text_area("Notas de Verificación", key=f"n_{contrato['id']}")
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("Validar y Enviar", key=f"v_{contrato['id']}", use_container_width=True):
                                    contratos_db[idx_real]['estado'] = 'Pendiente Autorización'
                                    contratos_db[idx_real]['comentarios'] = f"Cumplimiento: {coment}" if coment else ""
                                    guardar_datos(contratos_db)
                                    st.rerun()
                            with col_btn2:
                                if st.button("Rechazar", key=f"r_{contrato['id']}", use_container_width=True):
                                    contratos_db[idx_real]['estado'] = 'Rechazado'
                                    contratos_db[idx_real]['comentarios'] = f"Rechazo Cumplimiento: {coment}"
                                    guardar_datos(contratos_db)
                                    st.rerun()
                                
                        elif rol_actual == "3. Dirección Comercial":
                            st.write(f"**Historial de Notas:** {contrato['comentarios']}")
                            coment_dir = st.text_area("Observaciones de Dirección", key=f"nd_{contrato['id']}")
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("Autorizar", key=f"a_{contrato['id']}", use_container_width=True):
                                    contratos_db[idx_real]['estado'] = 'Para Facturar'
                                    if coment_dir:
                                        contratos_db[idx_real]['comentarios'] += f" | Dirección: {coment_dir}"
                                    guardar_datos(contratos_db)
                                    st.rerun()
                            with col_btn2:
                                if st.button("Rechazar", key=f"rd_{contrato['id']}", use_container_width=True):
                                    contratos_db[idx_real]['estado'] = 'Rechazado'
                                    contratos_db[idx_real]['comentarios'] += f" | Rechazo Dirección: {coment_dir}"
                                    guardar_datos(contratos_db)
                                    st.rerun()
                                
                        elif rol_actual == "4. Contabilidad":
                            st.write(f"**Historial de Notas:** {contrato['comentarios']}")
                            coment_cont = st.text_area("Observaciones de Contabilidad", key=f"nc_{contrato['id']}")
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("Facturado y Cerrar", key=f"f_{contrato['id']}", use_container_width=True):
                                    contratos_db[idx_real]['estado'] = 'Finalizado'
                                    if coment_cont:
                                        contratos_db[idx_real]['comentarios'] += f" | Contabilidad: {coment_cont}"
                                    guardar_datos(contratos_db)
                                    st.rerun()
                            with col_btn2:
                                if st.button("Rechazar", key=f"rc_{contrato['id']}", use_container_width=True):
                                    contratos_db[idx_real]['estado'] = 'Rechazado'
                                    contratos_db[idx_real]['comentarios'] += f" | Rechazo Contabilidad: {coment_cont}"
                                    guardar_datos(contratos_db)
                                    st.rerun()

                    with col_visor:
                        st.subheader("Visor de Documento")
                        # Llamamos a la función segura, pasándole el nombre original del archivo
                        display_pdf(contrato['archivo_b64'], contrato['archivo_nombre'])

    # --- TABLA DE TRAZABILIDAD ---
    st.markdown("---")
    
    col_titulo, col_actualizar = st.columns([5, 1])
    with col_titulo:
        st.subheader("📊 Tablero de Trazabilidad en Tiempo Real")
    with col_actualizar:
        st.write("") 
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.rerun()

    if contratos_db:
        # LÓGICA DE FILTRADO POR ROL
        if rol_actual == "1. Asesor Comercial":
            datos_trazabilidad = [c for c in contratos_db if c['asesor'] == nombre_actual]
        else:
            datos_trazabilidad = contratos_db
            
        if datos_trazabilidad:
            df = pd.DataFrame(datos_trazabilidad).drop(columns=['archivo_b64'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No tienes registros históricos en tu cuenta.")
    else:
        st.write("No hay registros activos en el sistema.")