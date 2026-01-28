import requests
import pandas as pd
from datetime import datetime
import json
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/person-statistics"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PARÂMETROS DE CONSULTA ===
params = {
    "CustomerCode": 575,      # Código do cliente (ou troque por CPF/CNPJ)
    "BranchCode": [2]
}

print("🚀 Iniciando consulta de Estatísticas de Cliente (Person Statistics)...")
print(f"📦 Parâmetros enviados:\n{json.dumps(params, indent=2)}")

# === REQUISIÇÃO GET ===
try:
    response = requests.get(URL, headers=headers, params=params, timeout=60)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão: {e}")
    sys.exit(1)

print(f"📡 Status HTTP: {response.status_code}")

if response.status_code != 200:
    print("❌ Erro na resposta da API:")
    print(response.text)
    sys.exit(1)

# === TRATAMENTO DO JSON ===
try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA DEBUG JSON ===
debug_file = f"debug_person_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === VALIDAÇÃO ===
if not isinstance(data, dict) or not data:
    print("⚠️ Nenhum dado retornado pela API.")
    sys.exit(0)

# === TRANSFORMA EM DATAFRAME ===
df_stats = pd.DataFrame([data])

# === MAPEAMENTO DE NOMES AMIGÁVEIS ===
rename_map = {
    "averageDelay": "Atraso Médio (dias)",
    "maximumDelay": "Maior Atraso (dias)",
    "purchaseQuantity": "Qtd. Compras",
    "purchasePiecesQuantity": "Qtd. Peças Compradas",
    "totalPurchaseValue": "Valor Total Compras",
    "averagePurchaseValue": "Valor Médio Compras",
    "biggestPurchaseDate": "Data Maior Compra",
    "biggestPurchaseValue": "Valor Maior Compra",
    "firstPurchaseDate": "Data Primeira Compra",
    "firstPurchaseValue": "Valor Primeira Compra",
    "lastPurchaseDate": "Data Última Compra",
    "lastPurchaseValue": "Valor Última Compra",
    "totalInstallmentsPaid": "Total Parcelas Pagas",
    "quantityInstallmentsPaid": "Qtd. Parcelas Pagas",
    "averageValueInstallmentsPaid": "Valor Médio Parcelas Pagas",
    "totalInstallmentsDelayed": "Total Parcelas Atrasadas",
    "quantityInstallmentsDelayed": "Qtd. Parcelas Atrasadas",
    "averageInstallmentDelay": "Atraso Médio Parcelas (dias)",
    "totalInstallmentsOpen": "Total Parcelas em Aberto",
    "quantityInstallmentsOpen": "Qtd. Parcelas em Aberto",
    "averageInstallmentsOpen": "Valor Médio Parcelas em Aberto",
    "lastInvoicePaidValue": "Valor Última Nota Paga",
    "lastInvoicePaidDate": "Data Última Nota Paga",
    "highestDebt": "Maior Dívida",
    "highestDebtDate": "Data Maior Dívida",
    "affiliateLimitAmount": "Limite Afiliado (R$)",
    "lastDebtNoticeDate": "Data Último Aviso de Dívida"
}

df_stats.rename(columns=rename_map, inplace=True)

# === REORDENA COLUNAS (mantendo lógica temporal) ===
ordered_columns = [
    "Qtd. Compras", "Qtd. Peças Compradas", "Valor Total Compras", "Valor Médio Compras",
    "Data Primeira Compra", "Valor Primeira Compra",
    "Data Última Compra", "Valor Última Compra",
    "Data Maior Compra", "Valor Maior Compra",
    "Atraso Médio (dias)", "Maior Atraso (dias)",
    "Total Parcelas Pagas", "Qtd. Parcelas Pagas", "Valor Médio Parcelas Pagas",
    "Total Parcelas Atrasadas", "Qtd. Parcelas Atrasadas", "Atraso Médio Parcelas (dias)",
    "Total Parcelas em Aberto", "Qtd. Parcelas em Aberto", "Valor Médio Parcelas em Aberto",
    "Valor Última Nota Paga", "Data Última Nota Paga",
    "Maior Dívida", "Data Maior Dívida",
    "Limite Afiliado (R$)", "Data Último Aviso de Dívida"
]

# Garante que as colunas que existam sejam ordenadas (nem todas podem vir na resposta)
df_stats = df_stats[[col for col in ordered_columns if col in df_stats.columns]]

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"person_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_stats.to_excel(writer, index=False, sheet_name="PersonStatistics")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print("🏁 Execução finalizada com sucesso.")
