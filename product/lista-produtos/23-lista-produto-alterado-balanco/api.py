import requests
import pandas as pd
import json
from datetime import datetime
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/omni-changed-balances"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "filter": {
        "change": {
            "startDate": "2024-08-01T00:00:00Z",
            "endDate": "2025-09-28T23:59:59Z",
            "balances": [
                {
                    "branchCode": 1,
                    "stockCodeList": [1]
                }
            ],
            "branchInfo": {"branchCode": 1, "isActive": True},
            "classifications": [
                {"type": 104, "codeList": ["001","002","003","004","005","006"]}
            ]
        },
    },
    "option": {
        "isTransaction": True,
        "isSalesOrder": True,
    },
    "order": "productCode"
}


print("🚀 Consultando saldos omni de produtos...")

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=90)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão com a API: {e}")
    sys.exit(1)

print(f"📡 Status HTTP: {response.status_code}")
if response.status_code != 200:
    print("❌ Erro na resposta da API:")
    print(response.text)
    sys.exit(1)

# === TRATAMENTO DO JSON ===
try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA DEBUG ===
debug_file = f"debug_omni_balances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum saldo retornado pela API.")
    sys.exit(0)

saldos = []
for item in items:
    saldos.append({
        "productCode": item.get("productCode"),
        "productSku": item.get("productSku"),
        "referenceCode": item.get("referenceCode"),
        "colorCode": item.get("colorCode"),
        "sizeName": item.get("sizeName"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate"),
        "branchCode": item.get("branchCode"),
        "stockCode": item.get("stockCode"),
        "stock": item.get("stock"),
        "salesOrder": item.get("salesOrder"),
        "inputTransaction": item.get("inputTransaction"),
        "outputTransaction": item.get("outputTransaction"),
        "avaliableStock": item.get("avaliableStock")
    })

# === CONVERTE PARA DATAFRAME ===
df_saldos = pd.DataFrame(saldos)

# === EXPORTA PARA EXCEL ===
excel_file = f"omni_changed_balances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_saldos.to_excel(writer, index=False, sheet_name="SaldosOmni")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
