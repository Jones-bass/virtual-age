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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/financial-panel/v2/average-payment-period/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === CORPO DA REQUISIÇÃO ===
payload = {
    "branchs": [5],  # 🔹 Informe os códigos das empresas que deseja consultar
    "datemin": "2025-10-01T00:00:00Z",
    "datemax": "2025-10-26T23:59:59Z"
}

print("🚀 Iniciando consulta de Período Médio de Pagamento (Painel Financeiro)...")
print(f"📦 Payload enviado:\n{json.dumps(payload, indent=2)}")

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=60)
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

# === SALVA DEBUG JSON ===
debug_file = f"debug_average_payment_period_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
data_rows = data.get("dataRow", [])
if data_rows:
    df_data = pd.DataFrame(data_rows)
    print(f"✅ {len(df_data)} registros encontrados em 'dataRow'")
else:
    df_data = pd.DataFrame()
    print("⚠️ Nenhum dado encontrado em 'dataRow'")

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"average_payment_period_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        if not df_data.empty:
            df_data.to_excel(writer, index=False, sheet_name="PeriodoMedio")
        else:
            pd.DataFrame([{"Aviso": "Nenhum dado retornado da API"}]).to_excel(writer, index=False, sheet_name="PeriodoMedio")

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")

print("🏁 Execução finalizada com sucesso.")
