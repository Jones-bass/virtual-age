import requests
import pandas as pd
import json
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/general/v2/transactions"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PARAMS = {
    "BranchCode": "1",                     # Código da filial
    "TransactionCode": "42289",            # Código da transação
    "TransactionDate": "2025-11-06T00:00:00Z",  # Data da transação (ISO)
    "Expand": "itemPromotionalEngines,originDestination",  # Expande detalhes
}

print("🚀 Iniciando consulta detalhada da transação TOTVS...")
print(f"📄 Parâmetros: {PARAMS}")

# === REQUISIÇÃO ===
response = requests.get(URL, headers=headers, params=PARAMS)
print(f"📡 Status HTTP: {response.status_code}")

if response.status_code != 200:
    print("❌ Erro ao consultar transação:")
    print(response.text)
    sys.exit(1)

try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === DEBUG: SALVAR JSON CRU (opcional, útil para inspeção) ===
debug_file = f"debug_transaction_{PARAMS['TransactionCode']}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Resposta completa salva em: {debug_file}")

# === DEBUG: INSPEÇÃO DE CHAVES ===
print("🔍 Estrutura principal da resposta:")
for key, value in data.items():
    tipo = type(value).__name__
    tamanho = len(value) if isinstance(value, (list, dict)) else "-"
    print(f"   - {key} ({tipo}) tamanho: {tamanho}")

print("-" * 60)

# === 1️⃣ DADOS PRINCIPAIS ===
main_fields = {
    "BranchCode": data.get("branchCode"),
    "TransactionCode": data.get("transactionCode"),
    "TransactionDate": data.get("transactionDate"),
    "CustomerCode": data.get("customerCode"),
    "OperationCode": data.get("operationCode"),
    "SellerCode": data.get("sellerCode"),
    "GuideCode": data.get("guideCode"),
    "PaymentConditionCode": data.get("paymentConditionCode"),
    "PriceTableCode": data.get("priceTableCode"),
    "Status": data.get("status"),
    "LastChangeDate": data.get("lastchangeDate"),
}

df_main = pd.DataFrame([main_fields])
print(f"✅ Dados principais extraídos: {len(df_main.columns)} campos.")

# === 2️⃣ ITENS (detalhes da venda) ===
if data.get("items"):
    df_items = pd.json_normalize(data["items"])
    print(f"🧾 Total de itens encontrados: {len(df_items)}")
else:
    df_items = pd.DataFrame()
    print("⚠️ Nenhum item encontrado na transação.")

# === 3️⃣ CAMPOS EXPANDIDOS (opcional: promotionalEngines e originDestination) ===
df_promos = pd.DataFrame()
df_orig_dest = pd.DataFrame()

if data.get("itemPromotionalEngines"):
    df_promos = pd.json_normalize(data["itemPromotionalEngines"])
    print(f"🎯 Total de promoções aplicadas: {len(df_promos)}")

if data.get("originDestination"):
    df_orig_dest = pd.json_normalize(data["originDestination"])
    print(f"🚚 Total de origens/destinos: {len(df_orig_dest)}")

# === 4️⃣ EXPORTAÇÃO PARA EXCEL ===
excel_file = f"transacao_{PARAMS['BranchCode']}_{PARAMS['TransactionCode']}.xlsx"

try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df_main.to_excel(writer, index=False, sheet_name="Dados Principais")
        if not df_items.empty:
            df_items.to_excel(writer, index=False, sheet_name="Itens")
        if not df_promos.empty:
            df_promos.to_excel(writer, index=False, sheet_name="Promocoes")
        if not df_orig_dest.empty:
            df_orig_dest.to_excel(writer, index=False, sheet_name="OrigemDestino")

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")
