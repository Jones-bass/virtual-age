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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/cost-center"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando centros de custo...")

# === PAGINAÇÃO ===
all_items = []
page = 1
page_size = 100  

while True:
    params = {
        "StartChangeDate": "2022-01-01T00:00:00Z",   
        "EndChangeDate": "2025-12-31T23:59:59Z",     
        "IsInactive": False,                          
        "Page": page,
        "PageSize": page_size
    }

    try:
        response = requests.get(URL, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        sys.exit(1)

    items = data.get("items", [])
    print(f"📄 Página {page} carregada ({len(items)} centros).")

    if not items:
        break

    all_items.extend(items)

    if not data.get("hasNext", False):
        break

    page += 1
    time.sleep(0.3)

print(f"✅ Total de centros de custo retornados: {len(all_items)}")

# === SALVA DEBUG ===
debug_file = f"debug_cost_center_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === TRATAMENTO DOS DADOS ===
cost_centers = []
classifications = []

for item in all_items:
    cost_centers.append({
        "code": item.get("code"),
        "description": item.get("description"),
        "class": item.get("class"),
        "classType": item.get("classType"),
        "indirectType": item.get("indirectType"),
        "isInactive": item.get("isInactive")
    })

    for c in item.get("classifications", []):
        classifications.append({
            "costCenterCode": item.get("code"),
            "typeCode": c.get("typeCode"),
            "typeDescription": c.get("typeDescription"),
            "code": c.get("code"),
            "description": c.get("description")
        })

# === CONVERTE PARA DATAFRAMES ===
df_centers = pd.DataFrame(cost_centers)
df_classifications = pd.DataFrame(classifications)

# === EXPORTA PARA EXCEL ===
excel_file = f"cost_centers_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_centers.to_excel(writer, index=False, sheet_name="CostCenters")
    if not df_classifications.empty:
        df_classifications.to_excel(writer, index=False, sheet_name="Classifications")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📦 Total de centros exportados: {len(df_centers)}")
