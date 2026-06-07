# app.py
import streamlit as st
import base64
import auth
import validators
import database

# --- INICIALIZAR BASE DE DATOS ---
database.init_db()

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Gestor Documental CP", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
    [data-testid="stMetricLabel"] p { font-size: 0.85rem !important; }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
if 'contrato_auditoria_seleccionado' not in st.session_state:
    st.session_state.contrato_auditoria_seleccionado = None
if 'modo_visor' not in st.session_state:
    st.session_state.modo_visor = False

def display_pdf(base64_pdf, nombre_archivo):
    """Ofrece un botón de descarga nativo para los PDF."""
    try:
        bytes_pdf = base64.b64decode(base64_pdf)
        st.download_button(
            label=f"📥 Descargar: {nombre_archivo}",
            data=bytes_pdf,
            file_name=nombre_archivo,
            mime="application/pdf",
            key=f"dl_{nombre_archivo}_{base64_pdf[:10]}" 
        )
    except Exception as e:
        st.error("Error al procesar el documento PDF.")

# --- PANTALLA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🏭 Sistema de Contratos CP</h1>", unsafe_allow_html=True)
    st.write("") 
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            usuario_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit_button = st.form_submit_button("Ingresar", use_container_width=True)
            if submit_button:
                usr_data = auth.autenticar_usuario(usuario_input, password_input)
                if usr_data:
                    st.session_state.logged_in = True
                    st.session_state.usuario_actual = usr_data
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
        st.markdown("""**Usuarios prueba:** `asesor1`, `contabilidad`, `comercial`, `produccion`, `fabrica1`, `facturacion1` (Clave: 123)""")

# --- APLICACIÓN PRINCIPAL ---
else:
    usuario_info = st.session_state.usuario_actual
    rol_actual = usuario_info["rol"]
    nombre_actual = usuario_info["nombre"]

    st.sidebar.title("Perfil de Usuario")
    st.sidebar.write(f"👤 **{nombre_actual}**")
    st.sidebar.write(f"💼 *{rol_actual}*")
    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.usuario_actual = None
        st.session_state.contrato_auditoria_seleccionado = None
        st.session_state.modo_visor = False
        st.rerun()

    st.title(f"🚀 Panel de Trabajo: {rol_actual}")

    # ==========================================
    # ROL: ASESOR COMERCIAL
    # ==========================================
    if rol_actual == "Asesor Comercial":
        st.header("📄 Gestión de Contratos")
        
        # --- VISTA 1: BANDEJA Y BUSCADOR (Solo visible si NO hay un contrato seleccionado) ---
        if 'contrato_activo' not in st.session_state:
            
            # BANDEJA DE CORRECCIONES DIRECTA
            rechazos = database.obtener_solicitudes(estado_filtro='PENDIENTE_ASESOR', asesor_filtro=nombre_actual)
            if rechazos:
                st.warning("⚠️ Tienes expedientes devueltos por auditoría que requieren corrección:")
                for r in rechazos:
                    col_rec1, col_rec2 = st.columns([4, 1])
                    with col_rec1:
                        st.error(f"**Contrato:** {r['numero_contrato']} - {r['cliente']} | **Motivo del Rechazo:** {r['comentarios']}")
                    with col_rec2:
                        if st.button(f"✏️ Corregir {r['numero_contrato']}", key=f"btn_corregir_{r['numero_contrato']}", use_container_width=True):
                            st.session_state['contrato_activo'] = database.buscar_contrato_erp(r['numero_contrato'])
                            st.rerun()
                st.divider()

            # BUSCADOR DE CONTRATOS NUEVOS
            st.subheader("Buscar Nuevo Contrato en ERP Ofima")
            col_busq1, col_busq2 = st.columns([3, 1])
            with col_busq1:
                num_contrato_busqueda = st.text_input("Número de Contrato (ej. CONT-001, CONT-002)", label_visibility="collapsed")
            with col_busq2:
                buscar_clicked = st.button("Buscar Contrato", use_container_width=True, type="secondary")
                
            if buscar_clicked:
                datos_erp = database.buscar_contrato_erp(num_contrato_busqueda)
                if datos_erp:
                    st.session_state['contrato_activo'] = datos_erp
                    st.rerun() 
                else:
                    st.error("Contrato no encontrado en el ERP Ofima.")
                    
        # --- VISTA 2: ZONA DE CARGA DOCUMENTAL ---
        else:
            c_activo = st.session_state['contrato_activo']
            docs_req_data = validators.obtener_documentos_requeridos(
                c_activo['es_banco'], c_activo['acumulado_anual'], c_activo['tipo_carroceria']
            )
            
            st.success(f"Trabajando en el contrato **{c_activo['numero_contrato']}** cargado con éxito.")
            st.divider()
            st.write(f"### 📋 Zona de Carga Documental: **{c_activo['numero_contrato']}** ({c_activo['cliente']})")
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Cliente", c_activo['cliente'])
            with m2: st.metric("Tipo de Carrocería", c_activo['tipo_carroceria'])
            with m3: st.metric("Valor del Pedido", f"${c_activo['valor_pedido']:,.2f}")
            with m4: st.metric("Acumulado Anual", f"${c_activo['acumulado_anual']:,.0f}")

            docs_existentes = database.obtener_documentos(c_activo['numero_contrato'])
            dict_docs_existentes = {d['tipo']: d for d in docs_existentes}

            st.write("---")
            archivos_para_enviar = {}
            columnas_carga = st.columns(3)
            
            for index, doc in enumerate(docs_req_data):
                col_index = index % 3
                with columnas_carga[col_index]:
                    st.markdown(f"**{doc['nombre']}**")
                    
                    if doc['nombre'] in dict_docs_existentes:
                        archivo_previo = dict_docs_existentes[doc['nombre']]
                        st.caption(f"🟢 *Conservando: {archivo_previo['nombre']}*")
                        archivos_para_enviar[doc['nombre']] = {"origen": "existente", "datos": archivo_previo}
                    else:
                        st.caption(f"❌ *Pendiente por cargar*")
                    
                    file = st.file_uploader(f"Reemplazar o cargar {doc['nombre']}", type=['pdf'], key=f"up_{c_activo['numero_contrato']}_{doc['nombre']}", label_visibility="collapsed")
                    
                    if file:
                        b64 = base64.b64encode(file.getvalue()).decode('utf-8')
                        archivos_para_enviar[doc['nombre']] = {"origen": "nuevo", "nombre": file.name, "b64": b64}
                        st.caption(f"🔄 *Listo para actualizar con: {file.name}*")

            st.write("")
            col_acc1, col_acc2 = st.columns([1, 3])
            with col_acc1:
                if st.button("❌ Cancelar / Volver", use_container_width=True):
                    del st.session_state['contrato_activo']
                    st.rerun()
            with col_acc2:
                if st.button("🚀 Validar Requisitos y Enviar a Contabilidad", use_container_width=True, type="primary"):
                    if len(archivos_para_enviar) < len(docs_req_data):
                        st.error("Error: Aún faltan documentos obligatorios por cargar en el expediente.")
                    else:
                        for tipo_doc, info in archivos_para_enviar.items():
                            if info["origen"] == "nuevo":
                                database.guardar_o_actualizar_documento(c_activo['numero_contrato'], tipo_doc, info["nombre"], info["b64"])
                        
                        database.registrar_solicitud(c_activo['numero_contrato'], nombre_actual, 'CONTABILIDAD', f"Enviado por el asesor. Listo para revisión.")
                        st.success("¡Expediente actualizado y enviado a Contabilidad con éxito!")
                        del st.session_state['contrato_activo']
                        st.rerun()

    # ==========================================
    # ROLES DE APROBACIÓN (Contabilidad, Comercial, Producción, Fábrica, Facturación)
    # ==========================================
    else:
        # Se separaron las configuraciones para que Fábrica y Facturación sean independientes 
        # pero compartan la misma vista y estado destino.
        config_roles = {
            "Contabilidad": {"estado_ver": "CONTABILIDAD", "estado_ok": "COMERCIAL"},
            "Dirección Comercial": {"estado_ver": "COMERCIAL", "estado_ok": "PRODUCCION"},
            "Producción": {"estado_ver": "PRODUCCION", "estado_ok": "FABRICA_FACTURACION"},
            "Fábrica": {"estado_ver": "FABRICA_FACTURACION", "estado_ok": None},
            "Facturación": {"estado_ver": "FABRICA_FACTURACION", "estado_ok": None}
        }
        cfg = config_roles.get(rol_actual)
        pendientes = database.obtener_solicitudes(estado_filtro=cfg["estado_ver"])
        
        if not pendientes:
            st.info("No tienes tareas o aprobaciones pendientes en tu bandeja de entrada.")
        else:
            for contrato in pendientes:
                with st.expander(f"📂 EXPEDIENTE EN REVISIÓN: {contrato['numero_contrato']} | Cliente: {contrato['cliente']}"):
                    col_info, col_visor = st.columns([1, 1]) 
                    with col_info:
                        st.subheader("📊 Datos de Verificación")
                        st.write(f"**Asesor Responsable:** {contrato['asesor']}")
                        st.write(f"**Carrocería Solicitada:** {contrato['tipo_carroceria']}")
                        st.write(f"**Monto del Pedido:** ${contrato['valor']:,.2f}")
                        if contrato['comentarios']:
                            st.info(f"**Notas del Historial:**\n{contrato['comentarios']}")
                        
                        if cfg["estado_ok"] is not None:
                            st.write("---")
                            coment = st.text_area("Añadir comentarios/observaciones (OBLIGATORIO)", key=f"obs_{contrato['numero_contrato']}", height=68)
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if st.button("🟢 Autorizar / Aprobar", key=f"ok_{contrato['numero_contrato']}", use_container_width=True):
                                    if not coment.strip(): st.error("⚠️ El comentario es obligatorio.")
                                    else:
                                        prefijo = f" | {rol_actual}: " if contrato['comentarios'] else f"{rol_actual}: "
                                        database.actualizar_estado_solicitud(contrato['numero_contrato'], cfg["estado_ok"], f"{contrato['comentarios']}{prefijo}{coment}")
                                        st.rerun()
                            with col_b2:
                                if st.button("🔴 Rechazar (Devolver a Asesor)", key=f"ko_{contrato['numero_contrato']}", use_container_width=True):
                                    if not coment.strip(): st.error("⚠️ El comentario es obligatorio.")
                                    else:
                                        prefijo_r = f" | Rechazo {rol_actual}: " if contrato['comentarios'] else f"Rechazo {rol_actual}: "
                                        database.actualizar_estado_solicitud(contrato['numero_contrato'], "PENDIENTE_ASESOR", f"{contrato['comentarios']}{prefijo_r}{coment}")
                                        st.rerun()
                    with col_visor:
                        st.subheader("📄 Documentación Adjunta")
                        docs = database.obtener_documentos(contrato['numero_contrato'])
                        for d in docs:
                            col_doc_txt, col_doc_btn = st.columns([2, 1])
                            with col_doc_txt: st.write(f"🗎 **{d['tipo']}**\n*{d['nombre']}*")
                            with col_doc_btn: display_pdf(d['b64'], d['nombre'])

    # ==========================================
    # SECCIÓN INFERIOR DINÁMICA: TABLA O VISOR
    # ==========================================
    st.markdown("---")
    todas_solicitudes = database.obtener_solicitudes()
    
    if st.session_state.modo_visor and st.session_state.contrato_auditoria_seleccionado:
        if st.button("⬅️ Volver a la Tabla", type="primary"):
            st.session_state.modo_visor = False
            st.rerun()
        contrato_seleccionado = st.session_state.contrato_auditoria_seleccionado
        con_datos = next((c for c in todas_solicitudes if c['numero_contrato'] == contrato_seleccionado), None)
        if con_datos:
            st.markdown(f"### 🔍 EXPEDIENTE HISTÓRICO: **{con_datos['numero_contrato']}**")
            col_hist1, col_hist2 = st.columns([1, 1])
            with col_hist1:
                st.write(f"**Asesor:** {con_datos['asesor']} | **Cliente:** {con_datos['cliente']}")
                st.write(f"**Estado:** `{con_datos['estado']}` | **Valor:** ${con_datos['valor']:,.2f}")
                st.text_area("Notas / Observaciones:", value=con_datos['comentarios'], height=150, disabled=True, key=f"bit_visor_{contrato_seleccionado}")
            with col_hist2:
                st.markdown("#### 📂 Archivos Adjuntos Custodiados")
                docs_historicos = database.obtener_documentos(contrato_seleccionado)
                for dh in docs_historicos:
                    c_t, c_b = st.columns([2, 1])
                    with c_t: st.write(f"▪ **{dh['tipo']}**\n*{dh['nombre']}*")
                    with c_b: display_pdf(dh['b64'], dh['nombre'])
    else:
        st.subheader("📊 Tablero de Trazabilidad General")
        datos_trazabilidad = database.obtener_solicitudes(asesor_filtro=nombre_actual) if rol_actual == "Asesor Comercial" else todas_solicitudes
        if datos_trazabilidad:
            header_cols = st.columns([1.2, 1.5, 1.2, 1.5, 1.5, 2.5, 1.5])
            with header_cols[0]: st.markdown("**Contrato**")
            with header_cols[1]: st.markdown("**Cliente**")
            with header_cols[2]: st.markdown("**Asesor**")
            with header_cols[3]: st.markdown("**Valor Pedido**")
            with header_cols[4]: st.markdown("**Estado Workflow**")
            with header_cols[5]: st.markdown("**Notas**")
            with header_cols[6]: st.markdown("**Acción**")
            st.markdown("<hr style='margin-top:2px; margin-bottom:8px;'/>", unsafe_allow_html=True)
            for c in datos_trazabilidad:
                row_cols = st.columns([1.2, 1.5, 1.2, 1.5, 1.5, 2.5, 1.5])
                with row_cols[0]: st.write(c['numero_contrato'])
                with row_cols[1]: st.write(c['cliente'])
                with row_cols[2]: st.write(c['asesor'])
                with row_cols[3]: st.write(f"${c['valor']:,.2f}")
                with row_cols[4]: st.write(f"`{c['estado']}`")
                with row_cols[5]: st.caption(c['comentarios'] if c['comentarios'] else "Sin comentarios")
                with row_cols[6]:
                    if st.button("👁️ Ver Expediente", key=f"btn_link_{c['numero_contrato']}", use_container_width=True):
                        st.session_state.contrato_auditoria_seleccionado = c['numero_contrato']
                        st.session_state.modo_visor = True
                        st.rerun()
                st.markdown("<hr style='margin-top:2px; margin-bottom:4px; opacity: 0.3;'/>", unsafe_allow_html=True)