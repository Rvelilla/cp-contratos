# database.py
import sqlite3
from datetime import datetime

DB_NAME = "cp_contratos.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Inicializa la base de datos y simula los datos del ERP Ofima."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        es_banco INTEGER NOT NULL,
        acumulado_anual REAL DEFAULT 0.0
    )""")
    
    # Tabla de Contratos (Simula ERP Ofima)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contratos (
        numero_contrato TEXT PRIMARY KEY,
        cliente_id INTEGER,
        tipo_carroceria TEXT NOT NULL,
        valor_pedido REAL NOT NULL,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )""")
    
    # Tabla de Solicitudes (Nuestro Workflow)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitudes (
        numero_contrato TEXT PRIMARY KEY,
        asesor TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_registro TEXT NOT NULL,
        comentarios TEXT,
        FOREIGN KEY (numero_contrato) REFERENCES contratos(numero_contrato)
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
    
    # Insertar Datos Base si está vacía
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO clientes (id, nombre, es_banco, acumulado_anual) VALUES (1, 'Bancolombia', 1, 500000000)")
        cursor.execute("INSERT INTO clientes (id, nombre, es_banco, acumulado_anual) VALUES (2, 'Disel Andina', 0, 80000000)")
        cursor.execute("INSERT INTO clientes (id, nombre, es_banco, acumulado_anual) VALUES (3, 'Renting', 0, 45000000)")
        
        cursor.execute("INSERT INTO contratos VALUES ('CONT-001', 1, 'Isotérmica', 120000000)") # Banco
        cursor.execute("INSERT INTO contratos VALUES ('CONT-002', 2, 'Furgón', 30000000)")     # No Banco, >75M Acumulado
        cursor.execute("INSERT INTO contratos VALUES ('CONT-003', 3, 'Estacas', 25000000)")    # No Banco, <75M Acumulado
        
    conn.commit()
    conn.close()

def buscar_contrato_erp(numero_contrato):
    """Busca los datos del contrato simulando la consulta a Ofima."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT c.numero_contrato, cl.nombre, cl.es_banco, cl.acumulado_anual, c.tipo_carroceria, c.valor_pedido
        FROM contratos c JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.numero_contrato = ?
    """
    cursor.execute(query, (numero_contrato,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"numero_contrato": row[0], "cliente": row[1], "es_banco": bool(row[2]), 
                "acumulado_anual": row[3], "tipo_carroceria": row[4], "valor_pedido": row[5]}
    return None

def registrar_solicitud(numero_contrato, asesor, estado, comentarios=""):
    conn = get_connection()
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT INTO solicitudes (numero_contrato, asesor, estado, fecha_registro, comentarios) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(numero_contrato) DO UPDATE SET 
        estado=excluded.estado, comentarios=excluded.comentarios, fecha_registro=excluded.fecha_registro
    """, (numero_contrato, asesor, estado, fecha, comentarios))
    conn.commit()
    conn.close()

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

def obtener_solicitudes(estado_filtro=None, asesor_filtro=None):
    """Obtiene las solicitudes uniendo datos del ERP y del Workflow."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.numero_contrato, s.asesor, s.estado, s.fecha_registro, s.comentarios,
               c.tipo_carroceria, c.valor_pedido, cl.nombre, cl.acumulado_anual
        FROM solicitudes s
        JOIN contratos c ON s.numero_contrato = c.numero_contrato
        JOIN clientes cl ON c.cliente_id = cl.id
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
            "tipo_carroceria": r[5], "valor": r[6], "cliente": r[7], "sagrilaft_req": r[8] > 75000000
        })
    return resultados

def obtener_documentos(numero_contrato):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tipo_documento, nombre_archivo, archivo_b64 FROM documentos WHERE numero_contrato = ?", (numero_contrato,))
    rows = cursor.fetchall()
    conn.close()
    return [{"tipo": r[0], "nombre": r[1], "b64": r[2]} for r in rows]