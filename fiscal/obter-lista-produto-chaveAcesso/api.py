import sys
import json
import time
import os
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
import pandas as pd
from dotenv import load_dotenv

# ================= CONFIG =================

load_dotenv()
TOKEN = os.getenv("TOKEN")

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/image/v2/product/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# Faixa de produtos (ajuste conforme sua realidade)
PRODUCT_START = 5000
PRODUCT_END = 9000

# Chunk/paginação
CHUNK_SIZE = 500
PAGE_SIZE = 100
TIMEOUT = 120

# Filtros do endpoint (ajuste)
TYPE_IMAGE_CODE_LIST = [1]  # ex.: [1]
QTD_IMG_RESULT = 50         # quantityImageResult

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 2  # base backoff

# Exportação de imagens (TODAS EM UMA ÚNICA PASTA)
IMG_DIR = Path("images-totvs")
IMG_DIR.mkdir(parents=True, exist_ok=True)

# ================= UTILS =================

def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def chunked(lst: List[int], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def safe_int(v) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None

def sanitize_filename(name: str) -> str:
    """
    Remove caracteres inválidos e limita tamanho.
    """
    if not name:
        return ""
    invalid = '<>:"/\\|?*\n\r\t'
    out = "".join("_" if c in invalid else c for c in str(name))
    out = out.strip().strip(".")
    return out[:180]

# ================= IMAGE SAVE =================

def _strip_data_uri(b64: str) -> str:
    if "," in b64:
        return b64.split(",", 1)[1]
    return b64

def _guess_ext_from_data_uri(b64: str) -> str:
    if b64.startswith("data:image/"):
        head = b64.split(",", 1)[0].lower()
        if "image/png" in head:
            return ".png"
        if "image/webp" in head:
            return ".webp"
        if "image/jpg" in head or "image/jpeg" in head:
            return ".jpg"
    return ".jpg"

def save_image_from_base64_single_folder(
    base64_str: str,
    original_image_name: Optional[str],
) -> str:
    """
    Salva imagem base64 em UMA ÚNICA PASTA (IMG_DIR) usando imageName como nome.
    Se existir duplicado, cria _2, _3...
    Retorna o caminho salvo.
    """
    if not base64_str:
        return ""

    try:
        ext = _guess_ext_from_data_uri(base64_str)
        raw_b64 = _strip_data_uri(base64_str)
        image_bytes = base64.b64decode(raw_b64)

        base_name = sanitize_filename(original_image_name or "")

        # Se não vier nome, cria um nome baseado em timestamp
        if not base_name:
            base_name = f"image_{datetime.now():%Y%m%d_%H%M%S_%f}"

        # garante extensão
        if not Path(base_name).suffix:
            file_name = f"{base_name}{ext}"
        else:
            file_name = base_name

        file_path = IMG_DIR / file_name

        # Se existir, cria variações _2, _3...
        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            n = 2
            while True:
                candidate = IMG_DIR / f"{stem}_{n}{suffix}"
                if not candidate.exists():
                    file_path = candidate
                    break
                n += 1

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        return str(file_path)

    except Exception as e:
        log(f"⚠️ Erro ao salvar imagem (imageName={original_image_name}): {e}")
        return ""

# ================= PAYLOAD =================

def make_payload(product_codes: List[int], page: int, page_size: int) -> Dict[str, Any]:
    return {
        "filter": {
            "productCodeList": product_codes,
            "typeImageCodeList": TYPE_IMAGE_CODE_LIST,
        },
        "option": {
            "quantityImageResult": QTD_IMG_RESULT
        },
        "page": page,
        "pageSize": page_size
    }

# ================= HTTP =================

def _post_with_retry(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"   🔄 Tentativa {attempt}")
            resp = requests.post(URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            log(f"   ⚠️ Erro: {e}")
            if attempt == MAX_RETRIES:
                log("   ❌ Máximo de tentativas atingido.")
                return None
            sleep_time = RETRY_DELAY * attempt
            log(f"   ⏳ Retry em {sleep_time}s...")
            time.sleep(sleep_time)
    return None

# ================= FETCH =================

def fetch_all_product_images(product_codes: List[int]) -> List[Dict[str, Any]]:
    all_items: List[Dict[str, Any]] = []

    log("🔎 Iniciando busca de imagens por produto")

    for chunk_index, product_chunk in enumerate(chunked(product_codes, CHUNK_SIZE), start=1):
        log(f"📦 Chunk {chunk_index} | Produtos {product_chunk[0]} → {product_chunk[-1]}")

        page = 1
        while True:
            payload = make_payload(product_chunk, page, PAGE_SIZE)
            log(f"   📄 Página {page}")

            data = _post_with_retry(payload)
            if not data:
                log("   ⛔ Sem resposta válida. Pulando chunk/página.")
                break

            items = data.get("items", []) or []
            has_next = bool(data.get("hasNext", False))

            if not items:
                log("   ⛔ Página sem itens. Encerrando chunk.")
                break

            all_items.extend(items)
            log(f"   ✅ Itens nesta página: {len(items)} | Total: {len(all_items)} | hasNext={has_next}")

            if not has_next or len(items) < PAGE_SIZE:
                log("   🏁 Encerrando chunk.")
                break

            page += 1
            time.sleep(0.25)

    log(f"✅ Total final de itens retornados: {len(all_items)}")
    return all_items

# ================= PROCESSAMENTO =================

def process_data_and_export_images(items: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    products_rows: List[Dict[str, Any]] = []
    images_rows: List[Dict[str, Any]] = []

    log("🧩 Processando itens e exportando imagens (uma pasta única)...")

    for it in items:
        product_code = safe_int(it.get("productCode")) or 0
        product_name = it.get("productName")
        images_list = it.get("images", []) or []

        products_rows.append({
            "productCode": product_code,
            "productName": product_name,
            "referencialGroupCode": it.get("referencialGroupCode"),
            "referencialCode": it.get("referencialCode"),
            "referencialName": it.get("referencialName"),
            "colorCode": it.get("colorCode"),
            "colorName": it.get("colorName"),
            "sizeName": it.get("sizeName"),
            "imagesCount": len(images_list),
        })

        for img in images_list:
            original_name = img.get("imageName")
            image_path = save_image_from_base64_single_folder(
                base64_str=img.get("imageFile"),
                original_image_name=original_name,
            )

            images_rows.append({
                "productCode": product_code,
                "productName": product_name,
                "imageCode": safe_int(img.get("imageCode")),
                "originalImageName": original_name,
                "imageDescription": img.get("imageDescription"),
                "typeImageCode": img.get("typeImageCode"),
                "typeImageName": img.get("typeImageName"),
                "imagePath": image_path,
            })

    return {
        "Products": pd.DataFrame(products_rows),
        "Images": pd.DataFrame(images_rows),
    }

# ================= MAIN =================

if __name__ == "__main__":
    if not TOKEN:
        log("❌ TOKEN não encontrado no .env (variável TOKEN).")
        sys.exit(1)

    log("🚀 Iniciando consulta /api/totvsmoda/image/v2/product/search")

    product_codes = list(range(PRODUCT_START, PRODUCT_END + 1))
    all_items = fetch_all_product_images(product_codes)

    debug_file = f"debug_product_images_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    log(f"💾 Debug salvo em: {debug_file}")

    if not all_items:
        log("⚠️ Nenhum item retornado.")
        sys.exit(0)

    dfs = process_data_and_export_images(all_items)

    excel_file = f"product_images_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        for name, df in dfs.items():
            if not df.empty:
                df.to_excel(writer, index=False, sheet_name=name)

    log(f"✅ Excel gerado: {excel_file}")
    log(f"📦 Products: {len(dfs['Products'])} | 🖼️ Images: {len(dfs['Images'])}")
    log(f"🗂️ Imagens salvas em: {IMG_DIR.resolve()}")