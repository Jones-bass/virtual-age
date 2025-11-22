import requests
import pandas as pd
from datetime import datetime
import json
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/classifications"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

params = {
    "StartChangeDate": "2024-01-01T00:00:00Z",
    "EndChangeDate": "2025-10-26T23:59:59Z",
    "TypeCodeList": [1, 2, 3, 4, 5],  
    "Page": 1,
    "PageSize": 100
}

print("🚀 Iniciando consulta de Classificações de Pessoa...")
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

# === SALVA DEBUG ===
debug_file = f"debug_classifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === INSPEÇÃO DE CHAVES ===
print("\n🔍 Estrutura principal da resposta:")
for key, value in data.items():
    tipo = type(value).__name__
    tamanho = len(value) if isinstance(value, (list, dict)) else "-"
    print(f"   - {key} ({tipo}) tamanho: {tamanho}")
print("-" * 60)

# === ESTRUTURAÇÃO DOS DADOS ===
items = data.get("items", [])
if items:
    df_classifications = pd.DataFrame(items)
    print(f"✅ {len(df_classifications)} registros encontrados na lista 'items'.")
else:
    df_classifications = pd.DataFrame()
    print("⚠️ Nenhum registro encontrado em 'items'.")

# === RENOMEAR COLUNAS (opcional) ===
if not df_classifications.empty:
    rename_map = {
        "typeCode": "Código do Tipo",
        "typeDescription": "Descrição do Tipo",
        "code": "Código da Classificação",
        "description": "Descrição da Classificação",
        "maxChangeFilterDate": "Data Máxima de Alteração"
    }
    df_classifications.rename(columns=rename_map, inplace=True)
    print("📝 Colunas renomeadas para nomes amigáveis.")

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"classifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        if not df_classifications.empty:
            df_classifications.to_excel(writer, index=False, sheet_name="Classifications")
        else:
            pd.DataFrame([{"Aviso": "Nenhum dado retornado da API"}]).to_excel(
                writer, index=False, sheet_name="Classifications"
            )

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")

print("🏁 Execução finalizada com sucesso.")
