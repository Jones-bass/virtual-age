import requests
import pandas as pd
import json
import sys
import os

# === CONFIGURAÇÕES ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === NOVA ROTA / ENDPOINT ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/sellers-list/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === REQUEST PAYLOAD ===
payload = {
    "branchs": [3]
}
# === REQUISIÇÃO ===
resp = requests.post(URL, headers=HEADERS, json=payload)
print("Status da requisição:", resp.status_code)

if resp.status_code != 200:
    print("❌ Erro na requisição:", resp.text)
    exit()

data = resp.json()

# === DEBUG: salvar JSON cru e mostrar resumo das chaves ===
debug_file = "debug_sellers.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 JSON cru salvo em: {debug_file}")

print("\n🔍 Estrutura do JSON retornado:")
for key, value in data.items():
    tipo = type(value).__name__
    tamanho = len(value) if isinstance(value, (list, dict)) else "-"
    print(f"   - {key} ({tipo}) tamanho: {tamanho}")
print("-" * 50)

# === TRATAMENTO DOS DADOS ===
dfs = {}  # dicionário para armazenar DataFrames

# 1️⃣ Dados principais
if "dataRow" in data and data["dataRow"]:
    df_sellers = pd.DataFrame(data["dataRow"])
    dfs["Sellers"] = df_sellers
    print(f"✅ Sellers encontrados: {len(df_sellers)} linhas")
else:
    print("⚠️ Nenhum seller encontrado para este payload")

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = "totvs_sellers_debug.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    for sheet_name, df in dfs.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"✅ Arquivo Excel gerado com sucesso: {excel_file}")
for sheet_name, df in dfs.items():
    print(f"   🧾 {sheet_name}: {len(df)} linhas")
