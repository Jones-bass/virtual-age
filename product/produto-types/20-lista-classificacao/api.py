import requests
import pandas as pd
import json
from datetime import datetime
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/classifications"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PARÂMETROS ===
params = {
    "startChangeDate": "2024-01-01T00:00:00Z",
    "endChangeDate": "2026-06-16T23:59:59Z",
    "typeCodeList": [102, 103],  # exemplo: listar tipos de classificação específicos
}

print("🚀 Consultando classificações de produtos...")

# === REQUISIÇÃO GET ===
try:
    response = requests.get(URL, headers=headers, params=params, timeout=60)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão com a API: {e}")
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
debug_file = f"debug_classifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhuma classificação retornada pela API.")
    sys.exit(0)

classificacoes = []
for item in items:
    classificacoes.append({
        "typeCode": item.get("typeCode"),
        "typeName": item.get("typeName"),
        "typeNameAux": item.get("typeNameAux"),
        "code": item.get("code"),
        "name": item.get("name"),
        "nameAux": item.get("nameAux"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

# === CONVERTE PARA DATAFRAME ===
df_classificacoes = pd.DataFrame(classificacoes)

# === EXPORTA PARA EXCEL ===
excel_file = f"product_classifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_classificacoes.to_excel(writer, index=False, sheet_name="Classificacoes")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
