import pdfplumber
import re
import io

def extraer_datos_oc(file_bytes):
    """Extrae información clave de un PDF de Orden de Compra."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    
    datos = {
        "numero_contrato": "PENDIENTE",
        "cliente": "DESCONOCIDO",
        "valor_pedido": 0.0
    }

    # 1. Extraer Número de Orden/Pedido
    # Buscamos un número de 7 a 10 dígitos que aparezca después de la etiqueta "Nº Orden de Compra"
    # El modificador [\s\S]+? permite saltar líneas o texto intermedio (como la palabra Fecha)
    match_oc = re.search(r"N[º°]\s*Orden\s*de\s*Compra[\s\S]+?(\d{7,10})", full_text, re.IGNORECASE)
    if match_oc:
        datos["numero_contrato"] = match_oc.group(1).strip()

    # 2. Extraer Cliente (Tras 'Proveedor:' según especificación de CP)
    match_cliente = re.search(r"Proveedor\s*:?\s*([^\n\r]+)", full_text, re.IGNORECASE)
    if match_cliente:
        datos["cliente"] = match_cliente.group(1).strip()

    # 3. Extraer Valor Total
    # Usamos \bTOTAL\b para evitar capturar "SUBTOTAL"
    # Buscamos el patrón numérico con comas/puntos que sigue a la palabra TOTAL
    match_valor = re.search(r"\bTOTAL\b\s*[:\s]*\$?\s*([\d\.,]+)", full_text, re.IGNORECASE)
    if match_valor:
        raw_val = match_valor.group(1)
        # Si el valor tiene múltiples comas (ej: 181,601,654), las eliminamos para poder convertirlo
        if raw_val.count(',') > 1:
            val_str = raw_val.replace(",", "")
        else:
            val_str = raw_val.replace(".", "").replace(",", ".")
        try:
            datos["valor_pedido"] = float(val_str)
        except:
            pass
            
    return datos