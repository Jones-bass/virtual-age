import os
import sys
import json
import time
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# ================= CONFIGURAÇÕES =================

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoice-products/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PRODUCT_START = 1
PRODUCT_END = 8000
CHUNK_SIZE = 500
PAGE_SIZE = 100
TIMEOUT = 120

MAX_RETRIES = 3
RETRY_DELAY = 2  # base para backoff

# ================= UTILIDADES =================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def chunked(lst: List[int], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# ================= PAYLOAD =================

def make_payload(product_codes: List[int], page: int, page_size: int) -> Dict[str, Any]:
    return {
        "filter": {
            "branchCodeList": [2],
            "ProductCodeList": product_codes,
            "startIssueDate": "2026-01-01T00:42:13.514Z",
            "endIssueDate": "2026-01-10T00:42:13.514Z",
             "operationCodeList": [
                    1, 10, 11, 18, 22, 100, 102, 104, 105, 107, 109, 110, 111, 112, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 128, 129, 130, 132, 134, 135, 138, 139, 140, 146, 147, 148, 151, 152, 153, 154, 155, 156, 157, 158, 159, 164, 165, 167, 168, 171, 172, 173, 174, 175, 176, 177, 178, 179, 181, 182, 183, 190, 201, 203, 221, 222, 223, 224, 504, 505, 507, 513, 551, 600, 601, 602, 603, 604, 605, 701, 702, 705, 706, 707, 708, 709, 991, 999, 1101, 1103, 1104, 1105, 1107, 1108, 1109, 1117, 1118, 1119, 1120, 1122, 1124, 1151, 1152, 1153, 1154, 1155, 1156, 1200, 1201, 1202, 1203, 1204, 1206, 1207, 1208, 1209, 1212, 1900, 1901, 1902, 1910, 1915, 1917, 1918, 1919, 1925, 1949, 1956, 2101, 2116, 2200, 3101, 3102, 3103, 3201, 5100, 5101, 5102, 5103, 5104, 5105, 5106, 5111, 5149, 5150, 5151, 5901, 5905, 5910, 5911, 5912, 5913, 5915, 5917, 5918, 5919, 5947, 5948, 5949, 5953, 5954, 5955, 5956, 5961, 5962, 5965, 5968, 5969, 5970, 5973, 5974, 5975, 5980, 5981, 6912, 7101
                ],
                   "invoiceStatusList": ["Issued"],
        },
        "expand": "batchItems",
        "order": "invoiceSequence",
        "page": page,
        "pageSize": page_size
    }

# ================= FETCH =================

def fetch_all_invoice_products(product_codes: List[int]) -> List[Dict[str, Any]]:
    all_items = []

    log("🔎 Iniciando busca de itens de NF")

    for chunk_index, product_chunk in enumerate(chunked(product_codes, CHUNK_SIZE), start=1):
        chunk_start = product_chunk[0]
        chunk_end = product_chunk[-1]

        log(f"📦 Chunk {chunk_index} | Produtos {chunk_start} → {chunk_end}")

        page = 1

        while True:
            payload = make_payload(product_chunk, page, PAGE_SIZE)

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    log(f"   🔄 Página {page} | Tentativa {attempt}")

                    response = requests.post(
                        URL,
                        headers=HEADERS,
                        json=payload,
                        timeout=TIMEOUT
                    )
                    response.raise_for_status()

                    data = response.json()
                    items = data.get("items", [])

                    if not items:
                        log("   ⛔ Página sem itens. Encerrando chunk.")
                        break

                    all_items.extend(items)

                    log(
                        f"   ✅ Página {page}: {len(items)} itens | "
                        f"Total acumulado: {len(all_items)}"
                    )

                    if len(items) < PAGE_SIZE:
                        log("   🏁 Última página do chunk.")
                        break

                    page += 1
                    time.sleep(0.3)
                    break  # sucesso → sai do retry

                except requests.exceptions.RequestException as e:
                    log(f"   ⚠️ Erro: {e}")

                    if attempt == MAX_RETRIES:
                        log("   ❌ Máximo de tentativas atingido. Pulando página.")
                        break

                    sleep_time = RETRY_DELAY * attempt
                    log(f"   ⏳ Retry em {sleep_time}s...")
                    time.sleep(sleep_time)

            else:
                break

            if len(items) < PAGE_SIZE:
                break

    log(f"✅ Total final de itens retornados: {len(all_items)}")
    return all_items

# ================= PROCESSAMENTO =================

def process_data(items: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    df_dicts = {
        "InvoiceProducts": [],
        "BatchItems": []
    }

    for item in items:
        df_dicts["InvoiceProducts"].append({
            "branchCode": item.get("branchCode"),
            "branchCnpj": item.get("branchCnpj"),
            "invoiceSequence": item.get("invoiceSequence"),
            "invoiceDate": item.get("invoiceDate"),
            "personCode": item.get("personCode"),
            "personName": item.get("personName"),
            "personCpfCnpj": item.get("personCpfCnpj"),
            "invoiceCode": item.get("invoiceCode"),
            "serialCode": item.get("serialCode"),
            "invoiceStatus": item.get("invoiceStatus"),
            "transactionBranchCode": item.get("transactionBranchCode"),
            "transactionDate": item.get("transactionDate"),
            "transactionCode": item.get("transactionCode"),
            "origin": item.get("origin"),
            "documentType": item.get("documentType"),
            "operationType": item.get("operationType"),
            "operationCode": item.get("operationCode"),
            "operatioName": item.get("operatioName"),
            "issueDate": item.get("issueDate"),
            "accessKey": item.get("accessKey"),
            "couponCode": item.get("couponCode"),
            "serialMachine": item.get("serialMachine"),
            "productCode": item.get("productCode"),
            "productName": item.get("productName"),
            "quantity": item.get("quantity"),
            "unitGrossValue": item.get("unitGrossValue"),
            "unitDiscountValue": item.get("unitDiscountValue"),
            "unitNetValue": item.get("unitNetValue"),
            "itemSequence": item.get("itemSequence"),
            "itemCode": item.get("itemCode"),
            "itemName": item.get("itemName"),
            "ncm": item.get("ncm"),
            "cfop": item.get("cfop"),
            "measureUnit": item.get("measureUnit"),
            "kitCode": item.get("kitCode"),
            "kitSequence": item.get("kitSequence"),
            "returnedQuantity": item.get("returnedQuantity"),
        })

        for b in item.get("batchItems", []):
            df_dicts["BatchItems"].append({
                "invoiceSequence": item.get("invoiceSequence"),
                "invoiceCode": item.get("invoiceCode"),
                "productCode": item.get("productCode"),
                "itemSequence": item.get("itemSequence"),
                "branchCode": b.get("branchCode"),
                "invoiceDate": b.get("invoiceDate"),
                "invoiceItemNumber": b.get("invoiceItemNumber"),
                "productCodeBatch": b.get("productCode"),
                "sequence": b.get("sequence"),
                "branchCodeBatch": b.get("branchCodeBatch"),
                "batchNumber": b.get("batchNumber"),
                "itemBatchNumber": b.get("itemBatchNumber"),
                "quantityBatch": b.get("quantityBatch"),
                "batchBarcode": b.get("batchBarcode")
            })

    return {name: pd.DataFrame(data) for name, data in df_dicts.items()}

# ================= MAIN =================

if __name__ == "__main__":
    log("🚀 Iniciando consulta de itens de NF")

    product_codes = list(range(PRODUCT_START, PRODUCT_END + 1))
    all_items = fetch_all_invoice_products(product_codes)

    debug_file = f"debug_invoice_products_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    log(f"💾 Debug salvo em: {debug_file}")

    if not all_items:
        log("⚠️ Nenhum item retornado.")
        sys.exit(0)

    dfs = process_data(all_items)

    excel_file = f"invoice_products_full_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        for name, df in dfs.items():
            if not df.empty:
                df.to_excel(writer, index=False, sheet_name=name)

    log(f"✅ Excel gerado: {excel_file}")
    log(f"📊 Total InvoiceProducts: {len(dfs['InvoiceProducts'])}")
