import json
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import os

# ==============================
# CONFIGURAÇÕES
# ==============================

load_dotenv()
TOKEN = os.getenv("TOKEN")

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoices/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ==============================
# LOG
# ==============================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ==============================
# PAYLOAD
# ==============================

def make_payload(page: int = 1, pageSize: int = 100) -> Dict[str, Any]:
    return {
        "filter": {
            "branchCodeList": [3, 5, 7],
            "operationCodeList": [
                111,112,151,551,504,505,701,702,5100,5101,5102,5103,5104,5105,5106,
                5111,5551,5953,5961,5962,5965,5974,5975,7101,
                119,120,121,171,172,173,182,183,221,222,1201,1202,
                1204,1207,1208,2200,2116
            ],
            "origin": "All",
            "eletronicInvoiceStatusList": ["Authorized"],
            "startIssueDate": "2026-02-01T00:00:00Z",
            "endIssueDate": "2026-02-28T23:59:59Z"
        },
        "page": page,
        "pageSize": pageSize,
        "order": "invoiceCode",
        "expand": "salesOrder"
    }

# ==============================
# BUSCA PAGINADA
# ==============================

def fetch_all_invoices() -> List[Dict[str, Any]]:
    all_items = []
    page = 1
    page_size = 100

    log("🧾 Iniciando busca de notas fiscais (somente salesOrder)...")

    while True:
        payload = make_payload(page, page_size)

        try:
            log(f"   - Buscando página {page}...")
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])

            if not items:
                log("   - Nenhum item retornado. Fim da busca.")
                break

            all_items.extend(items)
            log(f"   - {len(items)} registros retornados. Total acumulado: {len(all_items)}")

            if len(items) < page_size:
                break

            page += 1

        except requests.RequestException as e:
            log(f"❌ Erro na requisição: {e}")
            break

    log(f"✅ Total final de notas encontradas: {len(all_items)}")
    return all_items

# ==============================
# PROCESSA SOMENTE SALES ORDER
# ==============================

def process_sales_orders(nf: Dict[str, Any]) -> List[Dict[str, Any]]:
    processed = []
    sales_orders = nf.get("salesOrder", []) or []

    for so in sales_orders:
        processed.append({
            "Empresa": nf.get("branchCode"),
            "invoiceCode": nf.get("invoiceCode"),
            "Serie": nf.get("serialCode"),
            "IssueDate": nf.get("issueDate"),

            "OrderBranchCode": so.get("branchCode"),
            "OrderCode": so.get("orderCode"),
            "OrderId": so.get("orderId"),
            "CustomerOrderCode": so.get("customerOrderCode"),
        })

    return processed

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================

if __name__ == "__main__":
    log("🚀 Iniciando processo...")

    items = fetch_all_invoices()

    # Debug JSON
    debug_file = f"debug_salesorder_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    log(f"💾 Arquivo debug salvo: {debug_file}")

    # Processa sales orders
    all_sales_orders = []

    for nf in items:
        try:
            all_sales_orders.extend(process_sales_orders(nf))
        except Exception as e:
            log(f"⚠️ Erro ao processar invoice {nf.get('invoiceCode')}: {e}")

    df_sales = pd.DataFrame(all_sales_orders)

    # Exporta Excel
    excel_file = f"invoice_sales_orders_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    df_sales.to_excel(excel_file, index=False)

    log(f"✅ Excel gerado com sucesso: {excel_file}")
    log(f"📊 Total de sales orders exportados: {len(df_sales)}")