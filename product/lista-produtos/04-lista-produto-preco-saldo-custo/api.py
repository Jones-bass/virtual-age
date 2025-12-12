import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from auth.config import TOKEN

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    """Garante que o retorno seja sempre uma lista."""
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/costs/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando custos de produtos...")

# === REQUEST BODY ===
payload = {
    "filter": {
        "change": {
            "startDate": "2025-09-01T00:00:00Z",
            "endDate": "2025-09-30T23:59:59Z",
            "inBranchInfo": True,
            "branchInfoCodeList": [1],
        },
        "classifications": [
                {"type": 104, "codeList": ["001","002","003","004","005","006"]}
            ],
        "branchInfo": {"branchCode": 1, "isActive": True},
        },
        "option": {
            "costs": [
                {
                    "branchCode": 1,
                    "costCodeList": [7]
                }
            ],
        },
    "order": "productCode"
}

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=60)
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
debug_file = f"debug_costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA RESPOSTA ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum produto retornado pela API.")
    sys.exit(0)

# === TABELAS ===
produtos = []
custos = []

for item in items:
    produtos.append({
        "productCode": item.get("productCode"),
        "productName": item.get("productName"),
        "productSku": item.get("productSku"),
        "referenceCode": item.get("referenceCode"),
        "colorCode": item.get("colorCode"),
        "colorName": item.get("colorName"),
        "sizeName": item.get("sizeName"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

    for c in safe_list(item.get("costs")):
        custos.append({
            "productCode": item.get("productCode"),
            "branchCode": c.get("branchCode"),
            "costCode": c.get("costCode"),
            "costName": c.get("costName"),
            "cost": c.get("cost")
        })

# === CONVERTE PARA DATAFRAMES ===
df_produtos = pd.DataFrame(produtos)
df_custos = pd.DataFrame(custos)

# === EXPORTA PARA EXCEL ===
excel_file = f"product_costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    if not df_custos.empty:
        df_custos.to_excel(writer, index=False, sheet_name="Custos")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
