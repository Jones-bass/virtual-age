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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/composition-group-product"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

product_codes = list(range(100, 200))

params = {
    "productCodeList": [product_codes],       
    "page": 1,
    "pageSize": 100
}

print("🚀 Consultando composição de grupos de produto...")

all_items = []
page = 1

while True:
    params["page"] = page

    try:
        response = requests.get(URL, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro ao consultar API: {e}")
        sys.exit(1)

    # === SALVA DEBUG POR PÁGINA ===
    debug_name = f"debug_composition_group_{page}_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Debug salvo: {debug_name}")

    items = data.get("items", [])
    all_items.extend(items)

    if not data.get("hasNext"):
        break

    page += 1


if not all_items:
    print("⚠️ Nenhum dado retornado.")
    sys.exit(0)


# === SEPARA TABELAS ===
groups = []
compositions = []
items_composition = []

for item in all_items:
    group_code = item.get("groupCode")

    # Tabela principal: groups
    groups.append({
        "groupCode": group_code,
        "groupDescription": item.get("groupDescription"),
        "groupSequenceCode": item.get("groupSequenceCode"),
        "defaultProductCode": item.get("defaultProductCode"),
        "defaultProductDescription": item.get("defaultProductDescription")
    })

    # Lista compositions
    for comp in safe_list(item.get("compositions")):
        compositions.append({
            "groupCode": group_code,
            "codeOrder": comp.get("codeOrder"),
            "code": comp.get("code"),
            "description": comp.get("description"),
            "typeDescription": comp.get("typeDescription")
        })

        # Lista itemsComposition
        for ic in safe_list(comp.get("itemsComposition")):
            items_composition.append({
                "groupCode": group_code,
                "compositionCode": comp.get("code"),
                "fiberCode": ic.get("fiberCode"),
                "fiberDescription": ic.get("fiberDescription"),
                "fiberPercentage": ic.get("fiberPercentage")
            })


# === CONVERTE PARA DATAFRAMES ===
df_groups = pd.DataFrame(groups)
df_compositions = pd.DataFrame(compositions)
df_items_comp = pd.DataFrame(items_composition)

# === EXPORTA PARA EXCEL ===
excel_file = f"composition_group_product_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_groups.to_excel(writer, index=False, sheet_name="Groups")
    df_compositions.to_excel(writer, index=False, sheet_name="Compositions")
    df_items_comp.to_excel(writer, index=False, sheet_name="ItemsComposition")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
