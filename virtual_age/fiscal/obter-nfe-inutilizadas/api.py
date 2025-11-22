import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoices/disable"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando notas fiscais desabilitadas...")

# === PAGINAÇÃO ===
all_items = []
page = 1
page_size = 100

while True:
    params = {
        "StartDate": "2022-01-01T00:00:00Z",  # ajuste conforme necessário
        "EndDate": "2025-12-31T23:59:59Z",
        "BranchCodeList": [1],                # lista de empresas a consultar
        "Page": page,
        "PageSize": page_size,
        "Order": "branchCode,-maxChangeFilterDate"
    }

    try:
        response = requests.get(URL, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        sys.exit(1)

    items = data.get("items", [])
    print(f"📄 Página {page} carregada ({len(items)} itens).")

    if not items:
        break

    all_items.extend(items)

    if not data.get("hasNext", False):
        break

    page += 1
    time.sleep(0.3)

print(f"✅ Total de registros retornados: {len(all_items)}")

# === SALVA DEBUG ===
debug_file = f"debug_invoices_disable_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === TRATAMENTO DOS DADOS ===
invoices_disable = []

for item in all_items:
    invoices_disable.append({
        "branchCode": item.get("branchCode"),
        "branchCnpj": item.get("branchCnpj"),
        "initialInvoiceNumber": item.get("initialInvoiceNumber"),
        "finalInvoiceNumber": item.get("finalInvoiceNumber"),
        "serialCode": item.get("serialCode"),
        "documentType": item.get("documentType"),
        "receipt": item.get("receipt"),
        "receivementDate": item.get("receivementDate"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

# === CONVERTE PARA DATAFRAME ===
df = pd.DataFrame(invoices_disable)

# === EXPORTA PARA EXCEL ===
excel_file = f"invoices_disable_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
df.to_excel(excel_file, index=False)

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📦 Total de notas exportadas: {len(df)}")
