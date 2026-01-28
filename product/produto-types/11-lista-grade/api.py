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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/grid"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando grades de produto...")

# === PAGINAÇÃO ===
all_items = []
page = 1
page_size = 100

while True:
    params = {
        "StartChangeDate": "2022-09-01T00:00:00Z",
        "EndChangeDate": "2025-09-30T23:59:59Z",
        "Order": "code"
    }

    try:
        response = requests.get(URL, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        sys.exit(1)

    items = data.get("items", [])
    print(f"📄 Página {page} carregada ({len(items)} grades).")

    if not items:
        break

    all_items.extend(items)

    if not data.get("hasNext", False):
        break

    page += 1
    time.sleep(0.3)

print(f"✅ Total de grades retornadas: {len(all_items)}")

# === SALVA DEBUG ===
debug_file = f"debug_grid_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === TRATAMENTO DOS DADOS ===
grades = []

for item in all_items:
    grades.append({
        "code": item.get("code"),
        "name": item.get("name"),
        "type": item.get("type"),
        "grid": ", ".join(item.get("grid", [])) if isinstance(item.get("grid"), list) else item.get("grid"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

# === CONVERTE PARA DATAFRAME ===
df_grades = pd.DataFrame(grades)

# === EXPORTA PARA EXCEL ===
excel_file = f"grid_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
df_grades.to_excel(excel_file, index=False)

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📦 Total de grades exportadas: {len(df_grades)}")
