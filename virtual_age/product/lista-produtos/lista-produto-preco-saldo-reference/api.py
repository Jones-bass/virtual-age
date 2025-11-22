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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/references/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando referências de produtos...")

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
        "branchInfoCode": 1,
     
    },
    "order": "referenceCode"
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
debug_file = f"debug_references_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA RESPOSTA ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhuma referência retornada pela API.")
    sys.exit(0)

# === TABELAS ===
referencias = []
cores = []
produtos = []
composicoes = []
detalhes = []

for ref in items:
    referencias.append({
        "referenceCode": ref.get("ReferenceCode"),
        "name": ref.get("name"),
        "description": ref.get("description"),
        "descriptive": ref.get("descriptive"),
        "gridCode": ref.get("gridCode"),
        "weight": ref.get("weight"),
        "height": ref.get("height"),
        "width": ref.get("width"),
        "length": ref.get("length"),
        "insertDate": ref.get("insertDate"),
        "maxChangeFilterDate": ref.get("maxChangeFilterDate")
    })

    # === Detalhes ===
    for det in safe_list(ref.get("details")):
        detalhes.append({
            "referenceCode": ref.get("ReferenceCode"),
            "typeCode": det.get("typeCode"),
            "type": det.get("type"),
            "title": det.get("title"),
            "description": det.get("description")
        })

    # === Composição ===
    for comp in safe_list(ref.get("composition")):
        composicoes.append({
            "referenceCode": ref.get("ReferenceCode"),
            "material": comp.get("material"),
            "percentage": comp.get("percentage")
        })

    # === Cores e produtos ===
    for cor in safe_list(ref.get("colors")):
        cores.append({
            "referenceCode": ref.get("ReferenceCode"),
            "colorCode": cor.get("code"),
            "colorName": cor.get("name"),
            "groupName": cor.get("groupName"),
            "pantoneCode": cor.get("pantoneCode")
        })

        for prod in safe_list(cor.get("products")):
            produtos.append({
                "referenceCode": ref.get("ReferenceCode"),
                "colorCode": cor.get("code"),
                "productCode": prod.get("code"),
                "sku": prod.get("sku"),
                "productName": prod.get("name"),
                "size": prod.get("size"),
                "ncm": prod.get("ncm"),
                "ipi": prod.get("ipi"),
                "isActive": prod.get("isActive"),
                "insertDate": prod.get("insertDate"),
                "salesStartDate": prod.get("SalesStartDate"),
                "salesEndDate": prod.get("SalesEndDate"),
                "isBlocked": prod.get("isBlocked")
            })

# === CONVERTE PARA DATAFRAMES ===
df_referencias = pd.DataFrame(referencias)
df_detalhes = pd.DataFrame(detalhes)
df_composicoes = pd.DataFrame(composicoes)
df_cores = pd.DataFrame(cores)
df_produtos = pd.DataFrame(produtos)

# === EXPORTA PARA EXCEL ===
excel_file = f"product_references_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_referencias.to_excel(writer, index=False, sheet_name="Referencias")
    if not df_detalhes.empty:
        df_detalhes.to_excel(writer, index=False, sheet_name="Detalhes")
    if not df_composicoes.empty:
        df_composicoes.to_excel(writer, index=False, sheet_name="Composicao")
    if not df_cores.empty:
        df_cores.to_excel(writer, index=False, sheet_name="Cores")
    if not df_produtos.empty:
        df_produtos.to_excel(writer, index=False, sheet_name="Produtos")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
