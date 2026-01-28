import requests
import pandas as pd
import json
from datetime import datetime
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")


# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/general/v2/classifications"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PARÂMETROS ===
PARAMS = {
    "BranchCode": "2",                     # Código da filial
    "StartChangeDate": "2025-10-01T00:00:00Z",
    "EndChangeDate": "2025-10-30T23:59:59Z",
    "Page": 1,
    "PageSize": 100
}

print("🚀 Iniciando consulta de Tipos de Classificação (TRAFM101)...")
print(f"📄 Parâmetros: {PARAMS}")

# === REQUISIÇÃO ===
response = requests.get(URL, headers=headers, params=PARAMS)
print(f"📡 Status HTTP: {response.status_code}")

if response.status_code != 200:
    print("❌ Erro ao consultar tipos de classificação:")
    print(response.text)
    sys.exit(1)

try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA JSON COMPLETO PARA DEBUG ===
debug_file = f"debug_typeclassifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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

# === 1️⃣ DADOS PRINCIPAIS ===
main_fields = {
    "Count": data.get("count"),
    "TotalPages": data.get("totalPages"),
    "HasNext": data.get("hasNext"),
    "TotalItems": data.get("totalItems"),
}
df_main = pd.DataFrame([main_fields])
print(f"✅ Dados principais extraídos: {len(df_main.columns)} campos.")

# === 2️⃣ ITENS ===
if data.get("items"):
    df_items = pd.json_normalize(data["items"])
    print(f"🧾 Total de tipos encontrados: {len(df_items)}")
else:
    df_items = pd.DataFrame()
    print("⚠️ Nenhum tipo de classificação encontrado.")

# === 3️⃣ EXPORTAÇÃO PARA EXCEL ===
excel_file = f"typeclassifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df_main.to_excel(writer, index=False, sheet_name="Resumo")
        if not df_items.empty:
            df_items.to_excel(writer, index=False, sheet_name="Tipos")

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")
