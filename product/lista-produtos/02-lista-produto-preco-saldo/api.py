import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from auth.config import TOKEN

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    return value if isinstance(value, list) else []

# ============================================
# CONFIGURAÇÕES
# ============================================
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/balances/search"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

BRANCH_CODE = 1        # filial real
STOCK_CODE = 1         # código do estoque físico
PAGE_SIZE = 1000       # máximo permitido pela API

print("🚀 Iniciando consulta de estoque atual TOTVS...")

# ============================================
# PAGINAÇÃO
# ============================================
all_items = []
page = 1

while True:
    payload = {
        "filter": {
            "change": {
                "startDate": "2025-12-09T00:00:00Z",
                "endDate": "2025-12-09T23:59:59Z",
                "inBranchInfo": True,
                "branchInfoCodeList": [1],

                "inStock": True,
                "branchStockCodeList": [1],
                
                "stockCodeList": [1],
                "hasStock": True
            },
         
             
        },
        "option": {
            "balances": [
                {
                    "branchCode": 1,
                    "stockCodeList": [1],
                }
            ]
        },
        "order": "productCode",
        "page": page,
        "pageSize": PAGE_SIZE
    }

    print(f"📄 Consultando página {page}...")

    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar na API: {e}")
        sys.exit(1)

    items = data.get("items", [])

    if not items:
        print("⚠️ Nenhum dado encontrado nesta página.")
        break

    all_items.extend(items)

    if not data.get("hasNext", False):
        break

    page += 1
    time.sleep(0.2)

# ============================================
# RESULTADO
# ============================================
print(f"\n✅ Total de produtos retornados: {len(all_items)}")

debug_file = f"debug_balances_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)

print(f"💾 Debug salvo em: {debug_file}")

# ============================================
# ESTRUTURAÇÃO DOS DADOS
# ============================================
produtos = []
saldos = []
localizacoes = []
saldos_consolidados = []

for item in all_items:

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

    total_geral = 0

    for b in safe_list(item.get("balances")):

        estoque_atual = (
            (b.get("stock") or 0)
            + (b.get("inputTransaction") or 0)
            - (b.get("outputTransaction") or 0)
            - (b.get("salesOrder") or 0)
        )

        total_geral += estoque_atual

        saldos.append({
            "productCode": item.get("productCode"),
            "stock": b.get("stock"),
            "salesOrder": b.get("salesOrder"),
            "inputTransaction": b.get("inputTransaction"),
            "outputTransaction": b.get("outputTransaction"),
            "estoqueAtual": estoque_atual,
            "productionPlanning": b.get("productionPlanning"),
            "purchaseOrder": b.get("purchaseOrder"),
            "productionOrderProgress": b.get("productionOrderProgress"),
            "productionOrderWaitLib": b.get("productionOrderWaitLib"),
            "stockTemp": b.get("stockTemp"),
        })

    for loc in safe_list(item.get("locations")):
        localizacoes.append({
            "productCode": item.get("productCode"),
            "branchCode": loc.get("branchCode"),
            "locationCode": loc.get("locationCode"),
            "description": loc.get("description")
        })

    saldos_consolidados.append({
        "productCode": item.get("productCode"),
        "totalBalanceAllBranches": total_geral
    })

# ============================================
# DATAFRAMES
# ============================================
df_produtos = pd.DataFrame(produtos)
df_saldos = pd.DataFrame(saldos)
df_localizacoes = pd.DataFrame(localizacoes)
df_consolidados = pd.DataFrame(saldos_consolidados)

# Resumo por produto
if not df_saldos.empty:
    df_resumo = (
        df_saldos.groupby("productCode")
        .agg({
            "estoqueAtual": "sum",
            "stock": "sum",
            "salesOrder": "sum",
            "outputTransaction": "sum"
        })
        .reset_index()
    )
else:
    df_resumo = pd.DataFrame()

# ============================================
# EXPORTAÇÃO EXCEL
# ============================================
excel_file = f"estoque_atual_totvs_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    df_saldos.to_excel(writer, index=False, sheet_name="Saldos_Detalhados")
    df_localizacoes.to_excel(writer, index=False, sheet_name="Localizacoes")
    df_consolidados.to_excel(writer, index=False, sheet_name="Consolidado")
    df_resumo.to_excel(writer, index=False, sheet_name="Resumo_Estoque")

print(f"\n✅ Relatório gerado com sucesso: {excel_file}")
print(f"📦 Produtos: {len(df_produtos)}")
print(f"📊 Registros de saldos: {len(df_saldos)}")
print(f"📍 Localizações: {len(df_localizacoes)}")
