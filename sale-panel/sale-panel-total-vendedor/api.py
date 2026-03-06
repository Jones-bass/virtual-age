import requests
import pandas as pd
import json

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")


URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/totals-seller/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "branchs": [2,3,5,7],
    "datemin": "2024-09-01T00:00:00Z",
    "datemax": "2026-03-05T23:59:59Z"
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
# 1. Dados atuais
df_atual = pd.DataFrame(data.get("dataRow", []))
df_atual["periodo"] = "Atual"

# 2. Dados do ano anterior
df_anterior = pd.DataFrame(data.get("dataRowLastYear", []))
df_anterior["periodo"] = "Ano Anterior"

# 3. Totais agregados
totais = {
    "Periodo": ["Atual", "Ano Anterior"],
    "invoice_qty": [data["total"]["invoice_qty"], data["totalLastYear"]["invoice_qty"]],
    "invoice_value": [data["total"]["invoice_value"], data["totalLastYear"]["invoice_value"]],
    "itens_qty": [data["total"]["itens_qty"], data["totalLastYear"]["itens_qty"]],
    "tm": [data["total"]["tm"], data["totalLastYear"]["tm"]],
    "pa": [data["total"]["pa"], data["totalLastYear"]["pa"]],
    "pmpv": [data["total"]["pmpv"], data["totalLastYear"]["pmpv"]]
}
df_totais = pd.DataFrame(totais)

# === SALVA TUDO NO EXCEL ===
excel_file = "totvs_vendas_completo_debug.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_atual.to_excel(writer, sheet_name="Vendas_Atual", index=False)
    df_anterior.to_excel(writer, sheet_name="Vendas_Ano_Anterior", index=False)
    df_totais.to_excel(writer, sheet_name="Totais", index=False)

print(f"✅ Arquivo Excel gerado com sucesso: {excel_file}")
print(f"🧾 Linhas atuais: {len(df_atual)}, Ano anterior: {len(df_anterior)}")
