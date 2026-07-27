import pandas as pd
import re
import unicodedata
from rapidfuzz import fuzz
from reporte_farmacity.PRODUCTOS_DB import PRODUCTOS_DB


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
    eans_agregados = set()  # Evita duplicados

    # 1. SEGMENTACIÓN: Dividir el texto por delimitadores (, / ; + \n)
    chunks_raw = re.split(r"[,/;\n\+]+", str(texto))
    chunks = [normalizar_texto(c) for c in chunks_raw if c.strip()]

    for chunk in chunks:
        # Verificar palabras de exclusión
        if any(ex in chunk for ex in palabras_exclusion):
            continue

        # =========================================================================
        # 2. LÓGICA ESPECIAL: AGUA MICELAR
        # =========================================================================
        if "micelar" in chunk or fuzz.partial_ratio("micelar", chunk) > 85:
            aclara_180 = "180" in chunk
            aclara_400 = "400" in chunk

            if not aclara_180 and not aclara_400:
                p180 = next((p for p in PRODUCTOS_DB if "180 ML" in p["desc"]), None)
                p400 = next((p for p in PRODUCTOS_DB if "400 ML" in p["desc"]), None)
                for p in [p180, p400]:
                    if p and p["ean"] not in eans_agregados:
                        productos_encontrados.append(p)
                        eans_agregados.add(p["ean"])
            else:
                if aclara_180:
                    p180 = next((p for p in PRODUCTOS_DB if "180 ML" in p["desc"]), None)
                    if p180 and p180["ean"] not in eans_agregados:
                        productos_encontrados.append(p180)
                        eans_agregados.add(p180["ean"])
                if aclara_400:
                    p400 = next((p for p in PRODUCTOS_DB if "400 ML" in p["desc"]), None)
                    if p400 and p400["ean"] not in eans_agregados:
                        productos_encontrados.append(p400)
                        eans_agregados.add(p400["ean"])
            continue

        # =========================================================================
        # 3. LÓGICA ESPECIAL: DISTINCIÓN CREMA FACIAL UREA VS CREMA EMOLIENTE PS
        # =========================================================================
        es_ps_o_urea = any(term in chunk for term in ["urea", "emoliente", "ps", "facial ps", "crema ps"])
        if es_ps_o_urea:
            p_urea = next((p for p in PRODUCTOS_DB if p["cuf"] == "221171"), None)
            p_emoliente = next((p for p in PRODUCTOS_DB if p["cuf"] == "207677"), None)

            # Si el texto menciona explícitamente "urea" o "facial" -> Crema Facial Urea
            if "urea" in chunk or "facial" in chunk:
                if p_urea and p_urea["ean"] not in eans_agregados:
                    productos_encontrados.append(p_urea)
                    eans_agregados.add(p_urea["ean"])
                continue

            # Si menciona "emoliente", "490" o "corporal" -> Crema Emoliente PS
            if any(term in chunk for term in ["emoliente", "490", "corporal", "gran tamaño"]):
                if p_emoliente and p_emoliente["ean"] not in eans_agregados:
                    productos_encontrados.append(p_emoliente)
                    eans_agregados.add(p_emoliente["ean"])
                continue

            # Si dice únicamente "crema ps" o "ps" sin aclarar, asignamos la Emoliente 490 gr por defecto
            if "ps" in chunk:
                if p_emoliente and p_emoliente["ean"] not in eans_agregados:
                    productos_encontrados.append(p_emoliente)
                    eans_agregados.add(p_emoliente["ean"])
                continue

        # =========================================================================
        # 4. PROCESAMIENTO GENERAL DEL RESTO DEL CATÁLOGO
        # =========================================================================
        coincidencias_chunk = []

        for prod in PRODUCTOS_DB:
            # Saltear los que ya fueron procesados por lógica especial
            if "MICELAR" in prod["desc"] or prod["cuf"] in ["221171", "207677"]:
                continue

            for kw in prod.get("keywords", []):
                kw_norm = normalizar_texto(kw)
                kw_palabras = kw_norm.split()
                chunk_palabras = chunk.split()

                score_sort = fuzz.token_sort_ratio(kw_norm, chunk)
                todas_palabras_en_chunk = all(
                    w in chunk_palabras for w in kw_palabras
                )

                if score_sort >= umbral_similitud or todas_palabras_en_chunk:
                    coincidencias_chunk.append(
                        (len(kw_palabras), score_sort, prod)
                    )

        if coincidencias_chunk:
            coincidencias_chunk.sort(key=lambda x: (x[0], x[1]), reverse=True)
            mejor_prod = coincidencias_chunk[0][2]

            if mejor_prod["ean"] not in eans_agregados:
                productos_encontrados.append(mejor_prod)
                eans_agregados.add(mejor_prod["ean"])

    return productos_encontrados