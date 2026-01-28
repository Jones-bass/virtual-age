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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/legal-entities/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "filter": {
        "change": {
            "startDate": "2023-10-01T00:00:00Z",
            "endDate": "2025-10-26T23:59:59Z",
            "inAddress": True,
            "inPhone": True,
            "inObservation": True,
            "inPerson": True
        },
        "isCustomer": True,
        "isSupplier": True,
        "personCodeList": [110000002]
    },
    "option": {
        "branchStaticDataList": [0]
    },
    "expand": "addresses,phones,emails,observations,contacts,partners,socialNetworks",
    "order": "code",
    "page": 1,
    "pageSize": 100
}

print("🚀 Iniciando consulta de entidades jurídicas...")
print(f"📦 Payload enviado:\n{json.dumps(payload, indent=2)}")

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=60)
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

# === SALVA DEBUG ===
debug_file = f"debug_legal_entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === INSPEÇÃO DE CHAVES PRINCIPAIS ===
print("\n🔍 Estrutura principal da resposta:")
for key, value in data.items():
    tipo = type(value).__name__
    tamanho = len(value) if isinstance(value, (list, dict)) else "-"
    print(f"   - {key} ({tipo}) tamanho: {tamanho}")
print("-" * 60)

# === EXTRAÇÃO DE DADOS PRINCIPAIS ===
items = data.get("items", [])
if items:
    df_main = pd.json_normalize(items, sep="_", max_level=1)
    print(f"✅ {len(df_main)} registros encontrados na lista principal.")
else:
    df_main = pd.DataFrame()
    print("⚠️ Nenhum registro encontrado na lista principal.")

# === EXTRAÇÃO DE LISTAS ANINHADAS ===
nested_fields = ["addresses", "phones", "emails", "observations", "customerObservations",
                 "additionalFields", "classifications", "references", "relateds", "partners",
                 "contacts", "socialNetworks", "representatives"]

nested_dfs = {}

for field in nested_fields:
    nested_list = []
    for item in items:
        person_code = item.get("code")
        for entry in item.get(field) or []:  # garante que seja iterável
            entry["personCode"] = person_code
            nested_list.append(entry)
    if nested_list:
        nested_dfs[field] = pd.DataFrame(nested_list)
        print(f"📝 {field}: {len(nested_dfs[field])} registros extraídos.")
    else:
        nested_dfs[field] = pd.DataFrame()
        print(f"⚠️ {field}: nenhum registro encontrado.")

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"legal_entities_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        if not df_main.empty:
            df_main.to_excel(writer, index=False, sheet_name="LegalEntities")
        for key, df_nested in nested_dfs.items():
            if not df_nested.empty:
                df_nested.to_excel(writer, index=False, sheet_name=key)
    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")

print("🏁 Execução finalizada com sucesso.")
