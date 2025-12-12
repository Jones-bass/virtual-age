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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/price-tables/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando tabela de preços dos produtos...")

# === REQUEST BODY ===
payload = {
    "filter": {
        "change": {
            "startDate": "2022-09-01T00:00:00Z",
            "endDate": "2025-10-31T23:59:59Z",
            "inBranchInfo": True,
            "branchInfoCodeList": [2],
        },
        "branchInfo": {
            "branchCode": 2,
            "isActive": True
        }
    },
    "option": {
        "branchCodeList": [2],
        "priceTableCode": 1
    },
}


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
debug_file = f"debug_price_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA RESPOSTA ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum item retornado pela API.")
    sys.exit(0)

produtos = []
precos = []

for item in items:
    produtos.append({
        "productCode": item.get("productCode"),
        "productName": item.get("productName"),
        "productSku": item.get("productSku"),
        "referenceCode": item.get("referenceCode"),
        "colorCode": item.get("colorCode"),
        "colorName": item.get("colorName"),
        "sizeName": item.get("sizeName"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate"),
        "referenceId": item.get("referenceId")
    })

    for preco in safe_list(item.get("prices")):
        precos.append({
            "productCode": item.get("productCode"),
            "branchCode": preco.get("branchCode"),
            "originalPrice": preco.get("originalPrice"),
            "price": preco.get("price"),
            "scaleCode": preco.get("scaleCode")
        })

# === CONVERTE PARA DATAFRAMES ===
df_produtos = pd.DataFrame(produtos)
df_precos = pd.DataFrame(precos)

# === EXPORTA PARA EXCEL ===
excel_file = f"price_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    if not df_precos.empty:
        df_precos.to_excel(writer, index=False, sheet_name="Precos")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
