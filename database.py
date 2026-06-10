# database.py
import sqlite3
from datetime import datetime

# Cambiamos el nombre a v2 para forzar a Streamlit Cloud a crear una base de datos limpia
# y evitar el OperationalError por esquemas antiguos en archivos .db residuales.
DB_NAME = "cp_verificacion_v2.db"

def get_connection():
    # check_same_thread=False es crucial para que SQLite funcione correctamente
    # dentro del entorno multi-hilo de Streamlit, especialmente en la nube.
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    """Inicializa la base de datos local para la gestión de contratos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Tabla de Clientes (Local)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        nombre TEXT PRIMARY KEY,
        es_banco INTEGER NOT NULL,
        acumulado_anual REAL DEFAULT 0.0
    )""")
    
    # Tabla de Solicitudes (Contiene los datos extraídos y el estado del proceso)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitudes (
        numero_contrato TEXT PRIMARY KEY,
        cliente_nombre TEXT NOT NULL,
        asesor TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_registro TEXT NOT NULL,
        comentarios TEXT,
        tipo_carroceria TEXT,
        valor_pedido REAL,
        FOREIGN KEY (cliente_nombre) REFERENCES clientes(nombre)
    )""")

    # Tabla de Documentos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_contrato TEXT,
        tipo_documento TEXT NOT NULL,
        nombre_archivo TEXT NOT NULL,
        archivo_b64 TEXT NOT NULL,
        FOREIGN KEY (numero_contrato) REFERENCES solicitudes(numero_contrato)
    )""")
    
    conn.commit()
    conn.close()

def obtener_datos_cliente(nombre_cliente):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT es_banco, acumulado_anual FROM clientes WHERE nombre = ?", (nombre_cliente,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"es_banco": bool(row[0]), "acumulado_anual": row[1]}
    return None

def upsert_cliente(nombre, es_banco, acumulado_anual):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (nombre, es_banco, acumulado_anual) 
        VALUES (?, ?, ?)
        ON CONFLICT(nombre) DO UPDATE SET 
        es_banco=excluded.es_banco, acumulado_anual=excluded.acumulado_anual
    """, (nombre, int(es_banco), acumulado_anual))
    conn.commit()
    conn.close()

def registrar_solicitud(numero_contrato, cliente_nombre, asesor, estado, tipo_carroceria, valor_pedido, comentarios=""):
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT INTO solicitudes (numero_contrato, cliente_nombre, asesor, estado, fecha_registro, comentarios, tipo_carroceria, valor_pedido) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(numero_contrato) DO UPDATE SET 
        estado=excluded.estado, comentarios=excluded.comentarios, fecha_registro=excluded.fecha_registro,
        tipo_carroceria=excluded.tipo_carroceria, valor_pedido=excluded.valor_pedido
    """, (numero_contrato, cliente_nombre, asesor, estado, fecha, comentarios, tipo_carroceria, valor_pedido))
    conn.commit()
    conn.close()

def obtener_clientes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, es_banco, acumulado_anual FROM clientes ORDER BY nombre")
    rows = cursor.fetchall()
    conn.close()
    return [{"nombre": r[0], "es_banco": bool(r[1]), "acumulado_anual": r[2]} for r in rows]

def obtener_solicitudes(estado_filtro=None, asesor_filtro=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.numero_contrato, s.asesor, s.estado, s.fecha_registro, s.comentarios,
               s.tipo_carroceria, s.valor_pedido, s.cliente_nombre, cl.acumulado_anual, cl.es_banco
        FROM solicitudes s
        LEFT JOIN clientes cl ON s.cliente_nombre = cl.nombre
        WHERE 1=1
    """
    params = []
    if estado_filtro:
        query += " AND s.estado = ?"
        params.append(estado_filtro)
    if asesor_filtro:
        query += " AND s.asesor = ?"
        params.append(asesor_filtro)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    resultados = []
    for r in rows:
        resultados.append({
            "numero_contrato": r[0], "asesor": r[1], "estado": r[2], "fecha": r[3], "comentarios": r[4],
            "tipo_carroceria": r[5], "valor": r[6], "cliente": r[7], "acumulado_anual": r[8] or 0.0,
            "es_banco": bool(r[9])
        })
    return resultados
def actualizar_estado_solicitud(numero_contrato, nuevo_estado, nuevos_comentarios):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE solicitudes SET estado = ?, comentarios = ? WHERE numero_contrato = ?", 
                   (nuevo_estado, nuevos_comentarios, numero_contrato))
    conn.commit()
    conn.close()

# database.py (Reemplaza solo esta función)

def guardar_o_actualizar_documento(numero_contrato, tipo_documento, nombre_archivo, archivo_b64):
    """Guarda un documento o lo reemplaza si ya existía ese tipo para el contrato."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe este tipo de documento para el contrato
    cursor.execute("""
        SELECT id FROM documentos 
        WHERE numero_contrato = ? AND tipo_documento = ?
    """, (numero_contrato, tipo_documento))
    row = cursor.fetchone()
    
    if row:
        # Si existe, lo actualiza (reemplaza)
        cursor.execute("""
            UPDATE documentos 
            SET nombre_archivo = ?, archivo_b64 = ? 
            WHERE id = ?
        """, (nombre_archivo, archivo_b64, row[0]))
    else:
        # Si no existe, lo inserta nuevo
        cursor.execute("""
            INSERT INTO documentos (numero_contrato, tipo_documento, nombre_archivo, archivo_b64) 
            VALUES (?, ?, ?, ?)
        """, (numero_contrato, tipo_documento, nombre_archivo, archivo_b64))
        
    conn.commit()
    conn.close()

def obtener_documentos(numero_contrato):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tipo_documento, nombre_archivo, archivo_b64 FROM documentos WHERE numero_contrato = ?", (numero_contrato,))
    rows = cursor.fetchall()
    conn.close()
    return [{"tipo": r[0], "nombre": r[1], "b64": r[2]} for r in rows]