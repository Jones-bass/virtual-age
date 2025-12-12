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
code = "5118"        # código do produto
branch_code = 2       # código da filial

url = f"https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/products/{code}/{branch_code}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando produto...")

# === REQUISIÇÃO GET ===
try:
    response = requests.get(url, headers=headers, timeout=30)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão com a API: {e}")
    sys.exit(1)

print(f"📡 Status HTTP: {response.status_code}")
if response.status_code != 200:
    print(f"❌ Erro na resposta da API: {response.text}")
    sys.exit(1)

# === TRATAMENTO DO JSON ===
try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA DEBUG ===
debug_file = f"debug_product_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
produto = {
    "productCode": data.get("productCode"),
    "productName": data.get("productName"),
    "productSku": data.get("productSku"),
    "referenceCode": data.get("referenceCode"),
    "colorCode": data.get("colorCode"),
    "colorName": data.get("colorName"),
    "sizeName": data.get("sizeName"),
    "maxChangeFilterDate": data.get("maxChangeFilterDate"),
    "quantity": data.get("quantity"),
    "isBatchItem": data.get("isBatchItem"),
    "isPack": data.get("isPack"),
    "isRfid": data.get("isRfid"),
    "statusRfid": data.get("statusRfid")
}

# === Lotes ===
lotes = []
if data.get("batch"):
    b = data["batch"]
    lotes.append({
        "branchCode": b.get("branchCode"),
        "batchCode": b.get("batchCode"),
        "itemCode": b.get("itemCode"),
        "batchType": b.get("batchType"),
        "manufacturingDate": b.get("manufacturingDate"),
        "expirationDate": b.get("expirationDate"),
        "itemSupplierCode": b.get("itemSupplierCode"),
        "itemCustomerCode": b.get("itemCustomerCode")
    })

# === Packs ===
packs = []
if data.get("pack"):
    p = data["pack"]
    for item in safe_list(p.get("packItemList")):
        for sku in safe_list(item.get("productSkuList")):
            packs.append({
                "packNumber": p.get("packNumber"),
                "packDescription": p.get("packDescription"),
                "packType": p.get("packType"),
                "productCode": item.get("productCode"),
                "productName": item.get("productName"),
                "totalQuantity": item.get("totalQuantity"),
                "packItemNumber": sku.get("packItemNumber"),
                "productSku": sku.get("productSku"),
                "quantity": sku.get("quantity"),
                "statusRfid": sku.get("statusRfid")
            })

# === CONVERTE PARA DATAFRAMES ===
df_produto = pd.DataFrame([produto])
df_lotes = pd.DataFrame(lotes)
df_packs = pd.DataFrame(packs)

# === EXPORTA PARA EXCEL ===
excel_file = f"product_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produto.to_excel(writer, index=False, sheet_name="Produto")
    if not df_lotes.empty:
        df_lotes.to_excel(writer, index=False, sheet_name="Lotes")
    if not df_packs.empty:
        df_packs.to_excel(writer, index=False, sheet_name="Packs")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
