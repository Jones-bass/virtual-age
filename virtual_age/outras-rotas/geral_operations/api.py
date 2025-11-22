import requests
import pandas as pd
import json
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/general/v2/operations"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PAGE = 1
PAGE_SIZE = 100
all_records = []

while True:
    params = {
        "Order": "operationCode",
        "StartChangeDate": "2025-09-01T00:00:00Z",
        "EndChangeDate": "2025-11-30T00:00:00Z",
        "Expand": "calculations,values,balances,classifications",
        "Page": PAGE,
        "PageSize": PAGE_SIZE
    }
    
    print(f"\n📄 Buscando página {PAGE} de operações...")

    resp = requests.get(URL, headers=HEADERS, params=params)
    print("📡 Status HTTP:", resp.status_code)

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    try:
        data = resp.json()
    except Exception as e:
        print("❌ Erro ao decodificar JSON:", e)
        break

    # === SALVAR JSON CRU PARA DEBUG ===
    debug_file = f"debug_operations_page_{PAGE}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON cru salvo em: {debug_file}")

    # === INSPEÇÃO DAS CHAVES PRINCIPAIS ===
    print("🔍 Estrutura da resposta desta página:")
    for key, value in data.items():
        tipo = type(value).__name__
        tamanho = len(value) if isinstance(value, (list, dict)) else "-"
        print(f"   - {key} ({tipo}) tamanho: {tamanho}")
    print("-" * 50)

    records = data.get("items", [])
    if not records:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    all_records.extend(records)
    print(f"✅ Página {PAGE}: {len(records)} registros coletados")

    # Paginação
    if len(records) < PAGE_SIZE or not data.get("hasNext", False):
        print("✅ Paginação finalizada.")
        break

    PAGE += 1
    time.sleep(0.3)

# === CRIAÇÃO DO DATAFRAME PRINCIPAL ===
if not all_records:
    print("⚠️ Nenhum registro retornado da API.")
else:
    df_main = pd.json_normalize(all_records)

    # Converte colunas de datas
    for col in df_main.columns:
        if "date" in col.lower():
            df_main[col] = pd.to_datetime(df_main[col], errors="coerce")

    # === EXPANSÃO DOS CAMPOS ANINHADOS ===
    nested_fields = ["calculations", "values", "balances", "classifications"]
    nested_dfs = {}

    for field in nested_fields:
        nested_list = []
        for item in all_records:
            person_code = item.get("operationCode")
            for entry in item.get(field) or []:
                # Verifica se entry é um dicionário antes de modificar
                if isinstance(entry, dict):
                    entry["operationCode"] = person_code  # Adiciona código da operação para referência
                    nested_list.append(entry)
                else:
                    print(f"⚠️ {field} contém um item que não é um dicionário: {entry}")

        if nested_list:
            nested_dfs[field] = pd.json_normalize(nested_list)
            print(f"📝 {field}: {len(nested_dfs[field])} registros extraídos.")
        else:
            nested_dfs[field] = pd.DataFrame()
            print(f"⚠️ {field}: nenhum registro encontrado.")

    # === EXPORTAÇÃO PARA EXCEL ===
    excel_file = f"operacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            if not df_main.empty:
                df_main.to_excel(writer, index=False, sheet_name="Operations")
            for key, df_nested in nested_dfs.items():
                if not df_nested.empty:
                    df_nested.to_excel(writer, index=False, sheet_name=key)
        print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")

print("🏁 Execução finalizada com sucesso.")
