import requests
import pandas as pd
import json
from datetime import datetime
import sys
import time

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/composition-product"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando composição de produtos TOTVS...")

# === FUNÇÃO DE CONSULTA COM PAGINAÇÃO ===
def get_all_compositions():
    all_items = []
    page = 1

    while True:
        params = {
            "ProductCodeList": 13,
            "GroupCodeList": [],
            "ReferenceCodeList": []
        }

        try:
            response = requests.get(URL, headers=HEADERS, params=params, timeout=90)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na conexão: {e}")
            break

        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            break

        data = response.json()
        items = data.get("items", [])
        if not items:
            print("⚠️ Nenhum item encontrado nesta página.")
            break

        all_items.extend(items)

        if not data.get("hasNext", False):
            break

        page += 1
        time.sleep(0.3)

    return all_items


# === EXECUTA A COLETA ===
items = get_all_compositions()

if not items:
    print("⚠️ Nenhum dado retornado pela API.")
    sys.exit(0)

# === GERA NOMES DE ARQUIVOS ===
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
debug_file = f"debug_composition_product_{timestamp}.json"
excel_file = f"composition_product_{timestamp}.xlsx"

with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f"💾 JSON de debug salvo em: {debug_file}")

produtos = []
composicoes = []

for p in items:
    produtos.append({
        "productCode": p.get("productCode"),
        "productDescription": p.get("productDescription"),
        "groupCode": p.get("groupCode"),
        "groupSequenceCode": p.get("groupSequenceCode")
    })

    for comp in p.get("compositions", []):
        # Nível de composição
        composicoes.append({
            "productCode": p.get("productCode"),
            "compositionCodeOrder": comp.get("codeOrder"),
            "compositionCode": comp.get("code"),
            "compositionDescription": comp.get("description"),
            "compositionTypeDescription": comp.get("typeDescription"),
            "fiberCode": None,
            "fiberDescription": None,
            "fiberPercentage": None
        })

        # Nível de fibra (itemsComposition)
        for item_comp in comp.get("itemsComposition", []):
            composicoes.append({
                "productCode": p.get("productCode"),
                "compositionCodeOrder": comp.get("codeOrder"),
                "compositionCode": comp.get("code"),
                "compositionDescription": comp.get("description"),
                "compositionTypeDescription": comp.get("typeDescription"),
                "fiberCode": item_comp.get("fiberCode"),
                "fiberDescription": item_comp.get("fiberDescription"),
                "fiberPercentage": item_comp.get("fiberPercentage")
            })

# === CONVERTE PARA DATAFRAMES ===
df_produtos = pd.DataFrame(produtos)
df_composicoes = pd.DataFrame(composicoes)

# === EXPORTA EXCEL DIRETAMENTE NA RAIZ ===
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    if not df_composicoes.empty:
        df_composicoes.to_excel(writer, index=False, sheet_name="Composicoes")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📊 Total de produtos exportados: {len(df_produtos)}")
print(f"🧵 Total de composições exportadas: {len(df_composicoes)}")
