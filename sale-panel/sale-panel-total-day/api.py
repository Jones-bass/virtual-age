import requests
import pandas as pd
from datetime import datetime, timezone
import json
import sys
import os

# === CONFIGURAÇÕES ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/weekdays/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "branchs": [3],
    "datemin": "2025-09-01T00:00:00Z",
    "datemax": "2025-09-30T23:59:59Z"
}

# === REQUISIÇÃO ===
resp = requests.post(URL, headers=HEADERS, json=payload)
print("Status da requisição:", resp.status_code)

if resp.status_code != 200:
    print("❌ Erro na requisição:", resp.text)
    exit()

data = resp.json()

# === DEBUG: salvar JSON cru e mostrar resumo das chaves ===
debug_file = "debug_totals_seller.json"
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
# DataFrame dos dados atuais
df_atual = pd.DataFrame(data.get("dataRow", []))
df_atual["periodo"] = "Atual"

# Totais agregados
df_totais = pd.DataFrame([{
    "Periodo": "Atual",
    "invoiceQuantity": data.get("invoiceQuantity", 0),
    "invoiceValue": data.get("invoiceValue", 0),
    "itemQuantity": data.get("itemQuantity", 0)
}])

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = "totvs_vendas_debug.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_atual.to_excel(writer, sheet_name="Vendas_Atual", index=False)
    df_totais.to_excel(writer, sheet_name="Totais", index=False)

print(f"✅ Arquivo Excel gerado com sucesso: {excel_file}")
print(f"🧾 Linhas de dados atuais: {len(df_atual)}, Totais: {len(df_totais)}")
