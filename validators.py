# validators.py

def obtener_documentos_requeridos(es_banco, acumulado_anual, tipo_carroceria):
    """
    Determina la lista de documentos obligatorios detallando la razón de su condicionalidad.
    Retorna una lista de diccionarios con el nombre del requisito y su motivo.
    """
    documentos = []
    tipo_carroceria_str = str(tipo_carroceria).lower()
    
    # El documento base 'Pedido' siempre va
    documentos.append({"nombre": "Pedido", "motivo": "Requisito base obligatorio"})
    
    if es_banco:
        documentos.append({"nombre": "Orden de Compra", "motivo": "Obligatorio para entidades bancarias"})
    else:
        documentos.append({"nombre": "Términos y Condiciones", "motivo": "Obligatorio para Clientes No Banco"})
        # Ajuste de flexibilidad: Se presenta unificado para permitir que sea uno, el otro o ambos
        documentos.append({"nombre": "Soporte de Pago", "motivo": "Obligatorio para No Banco (Soporte de anticipo)"})
        
        # Regla Sagrilaf condicional por monto anual
        if acumulado_anual > 75000000:
            documentos.append({"nombre": "Soporte SAGRILAFT", "motivo": f"Requerido: El acumulado anual (${acumulado_anual:,.0f}) supera los 75M"})
            
    # Regla técnica de ingeniería condicional por tipo de producto
    if "isotermica" in tipo_carroceria_str or "isotérmica" in tipo_carroceria_str:
        documentos.append({"nombre": "Plano del Termo", "motivo": f"Requerido: Diseño técnico para carrocería {tipo_carroceria}"})
        
    return documentos