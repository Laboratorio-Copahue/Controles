import pprint
import pandas as pd


def generar_kits_config(
    excel_path="data/maestro_productos.xlsx", output_path="kits_config.py"
):
    # Intentar leer la primera hoja del Excel asegurando tipo string para no perder ceros a la izquierda ni formato de EAN/CUF
    try:
        df = pd.read_excel(excel_path, dtype=str)
    except FileNotFoundError:
        # Por si el archivo tuviera la errata tipográfica 'MAESTRO_PRODCUCTOS.XLSX'
        df = pd.read_excel("data/maestro_productos.xlsx", dtype=str)

    # Normalizar los nombres de las columnas (eliminar espacios extra)
    df.columns = df.columns.str.strip()

    kits_estructura = {}
    productos_maestro = {}
    productos_db = []

    # Detectar dinámicamente el nombre exacto de la columna de productos del kit por si varía levemente la tipografía
    col_prod_kit = (
        "PRODCUTOS DEL KIT"
        if "PRODCUTOS DEL KIT" in df.columns
        else "PRODUCTOS DEL KIT"
    )

    for _, row in df.iterrows():
        # Validar SKU
        sku_val = row.get("SKU")
        if pd.isna(sku_val) or not str(sku_val).strip():
            continue

        sku_int = int(float(str(sku_val).strip()))

        # Obtener campos limpiando espacios y valores nulos
        nombre_shopify = (
            str(row.get("NOMBRE SHOPIFY", "")).strip()
            if pd.notna(row.get("NOMBRE SHOPIFY"))
            else ""
        )
        cuf = (
            str(row.get("CUF", "")).strip()
            if pd.notna(row.get("CUF"))
            else ""
        )
        ean = (
            str(row.get("EAN", "")).strip()
            if pd.notna(row.get("EAN"))
            else ""
        )
        desc_db = (
            str(row.get("DESCRIPCIÓN DB", "")).strip()
            if pd.notna(row.get("DESCRIPCIÓN DB"))
            else ""
        )
        keywords_raw = (
            str(row.get("KEYWORDS DB", "")).strip()
            if pd.notna(row.get("KEYWORDS DB"))
            else ""
        )
        prod_kit_raw = (
            str(row.get(col_prod_kit, "")).strip()
            if pd.notna(row.get(col_prod_kit))
            else ""
        )

        # 1. Armar PRODUCTOS_MAESTRO
        if nombre_shopify:
            productos_maestro[sku_int] = nombre_shopify

        # 2. Armar KITS_ESTRUCTURA
        if prod_kit_raw:
            try:
                componentes = [
                    int(float(k.strip()))
                    for k in prod_kit_raw.split(",")
                    if k.strip()
                ]
                kits_estructura[sku_int] = componentes
            except ValueError:
                pass  # Si el contenido no es puramente numérico se salta

        # 3. Armar PRODUCTOS_DB
        if desc_db:
            keywords = (
                [k.strip() for k in keywords_raw.split(",") if k.strip()]
                if keywords_raw
                else []
            )
            productos_db.append(
                {
                    "cuf": cuf,
                    "ean": ean,
                    "desc": desc_db,
                    "keywords": keywords,
                }
            )

    # Formatear de manera elegante los diccionarios para el archivo final
    formatter = pprint.PrettyPrinter(indent=4, width=120)

    contenido_py = f"""# kits_config.py

# Estructura: ID_DEL_KIT: [Lista de IDs de productos que lo componen]
KITS_ESTRUCTURA = {formatter.pformat(kits_estructura)}

# Mapeo de nombres de kits en Shopify y sus componentes
KITS_SHOPIFY = {{}}

PRODUCTOS_MAESTRO = {formatter.pformat(productos_maestro)}

PRODUCTOS_DB = {formatter.pformat(productos_db)}
"""

    # Escribir el archivo final en UTF-8
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(contenido_py)

    print(
        f"Archivo '{output_path}' generado correctamente desde el Excel ingresado."
    )


