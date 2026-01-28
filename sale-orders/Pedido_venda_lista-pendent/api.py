import requests
import pandas as pd
import json
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")


# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sales-order/v2/pending-items"


headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PARÂMETROS ===
PARAMS = {
    "BranchCode": 2,    # Código da filial
    "OrderCode": 651    # Número do pedido
}

print("🚀 Iniciando consulta de Pedido de Venda (PEDFM001)...")
print(f"📄 Parâmetros: {PARAMS}")

# === REQUISIÇÃO ===
response = requests.get(URL, headers=headers, params=PARAMS)
print(f"📡 Status HTTP: {response.status_code}")

if response.status_code != 200:
    print("❌ Erro ao consultar pedido:")
    print(response.text)
    sys.exit(1)

try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA JSON PARA DEBUG ===
debug_file = f"debug_order_{PARAMS.get('OrderCode', 'byId')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Resposta completa salva em: {debug_file}")
# === INSPEÇÃO DE CHAVES ===
print("🔍 Estrutura principal da resposta:")
for key, value in data.items():
    tipo = type(value).__name__
    tamanho = len(value) if isinstance(value, (list, dict)) else "-"
    print(f"   - {key} ({tipo}) tamanho: {tamanho}")
print("-" * 60)

# === 1️⃣ DADOS PRINCIPAIS DO PEDIDO ===
main_fields = {
    "BranchCode": data.get("branchCode"),
    "OrderCode": data.get("orderCode"),
    "OrderId": data.get("orderId"),
}
df_main = pd.DataFrame([main_fields])
print(f"✅ Dados principais extraídos: {len(df_main.columns)} campos.")

# === 2️⃣ ITENS DO PEDIDO ===**
if data.get("items"):
    df_items = pd.json_normalize(data["items"])
    print(f"🧾 Total de itens encontrados: {len(df_items)}")
else:
    df_items = pd.DataFrame()
    print("⚠️ Nenhum item encontrado no pedido.")

# === 3️⃣ EXPORTAÇÃO PARA EXCEL ===
excel_file = f"pedido_{PARAMS['BranchCode']}_{PARAMS['OrderCode']}.xlsx"

try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df_main.to_excel(writer, index=False, sheet_name="Pedido")
        if not df_items.empty:
            df_items.to_excel(writer, index=False, sheet_name="Itens")

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")
