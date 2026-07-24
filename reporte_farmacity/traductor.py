import pandas as pd
import re
import unicodedata
from rapidfuzz import fuzz
from reporte_farmacity.PRODUCTOS_DB import PRODUCTOS_DB  # Asegúrate de tener este archivo con la base de datos de productos
# Base de datos optimizada de productos



def normalizar_texto(texto):
    """Limpia tildes, símbolos y convierte a minúsculas"""
    if not texto or not isinstance(texto, str):
        return ""
    texto_norm = unicodedata.normalize("NFD", texto)
    texto_sin_tildes = "".join(
        c for c in texto_norm if unicodedata.category(c) != "Mn"
    )
    texto_limpio = re.sub(r"[^a-z0-9\s]", " ", texto_sin_tildes.lower())
    return " ".join(texto_limpio.split())


def buscar_productos_en_texto(texto, umbral_similitud=80):
    """Analiza el texto fragmentado por ítems y retorna los productos detectados sin falsos positivos."""
    if pd.isna(texto) or not str(texto).strip():
        return []

    palabras_exclusion = ["deje", "cambio", "entrega", "tester", "test"]
    productos_encontrados = []
    eans_agregados = set()  # Evita duplicados en la respuesta final

    # 1. SEGMENTACIÓN: Dividir el texto por delimitadores (, / ; + \n)
    chunks_raw = re.split(r"[,/;\n\+]+", str(texto))
    chunks = [normalizar_texto(c) for c in chunks_raw if c.strip()]

    for chunk in chunks:
        # Verificar palabras de exclusión dentro de este fragmento
        if any(ex in chunk for ex in palabras_exclusion):
            continue

        # --- LÓGICA ESPECIAL PARA AGUA MICELAR EN EL CHUNK ---
        if "micelar" in chunk or fuzz.partial_ratio("micelar", chunk) > 85:
            aclara_180 = "180" in chunk
            aclara_400 = "400" in chunk

            if not aclara_180 and not aclara_400:
                p180 = next(
                    (p for p in PRODUCTOS_DB if "180 ML" in p["desc"]), None
                )
                p400 = next(
                    (p for p in PRODUCTOS_DB if "400 ML" in p["desc"]), None
                )
                for p in [p180, p400]:
                    if p and p["ean"] not in eans_agregados:
                        productos_encontrados.append(p)
                        eans_agregados.add(p["ean"])
            else:
                if aclara_180:
                    p180 = next(
                        (p for p in PRODUCTOS_DB if "180 ML" in p["desc"]), None
                    )
                    if p180 and p180["ean"] not in eans_agregados:
                        productos_encontrados.append(p180)
                        eans_agregados.add(p180["ean"])
                if aclara_400:
                    p400 = next(
                        (p for p in PRODUCTOS_DB if "400 ML" in p["desc"]), None
                    )
                    if p400 and p400["ean"] not in eans_agregados:
                        productos_encontrados.append(p400)
                        eans_agregados.add(p400["ean"])
            continue

        # --- PROCESAMIENTO DEL RESTO DEL CATÁLOGO POR CHUNK ---
        coincidencias_chunk = []

        for prod in PRODUCTOS_DB:
            if "MICELAR" in prod["desc"]:
                continue

            for kw in prod["keywords"]:
                kw_norm = normalizar_texto(kw)
                kw_palabras = kw_norm.split()
                chunk_palabras = chunk.split()

                # Comparar similitud con el fragmento individual
                score_sort = fuzz.token_sort_ratio(kw_norm, chunk)

                # Comprobar si todas las palabras clave están presentes dentro del fragmento
                todas_palabras_en_chunk = all(
                    w in chunk_palabras for w in kw_palabras
                )

                if score_sort >= umbral_similitud or todas_palabras_en_chunk:
                    coincidencias_chunk.append(
                        (len(kw_palabras), score_sort, prod)
                    )

        # Si hubo varias coincidencias en el fragmento, seleccionar la más específica
        if coincidencias_chunk:
            coincidencias_chunk.sort(key=lambda x: (x[0], x[1]), reverse=True)
            mejor_prod = coincidencias_chunk[0][2]

            if mejor_prod["ean"] not in eans_agregados:
                productos_encontrados.append(mejor_prod)
                eans_agregados.add(mejor_prod["ean"])

    return productos_encontrados