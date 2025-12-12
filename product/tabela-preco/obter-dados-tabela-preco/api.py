import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/price-tables-headers"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PARAMS = {
    "StartChangeDate": "2023-09-01T00:00:00Z",
    "EndChangeDate": "2025-10-31T23:59:59Z",
}

# === FUNÇÕES AUXILIARES ===
def fetch_page(url, headers, params):
    """Executa requisição GET com tratamento de erro."""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        sys.exit(1)

def get_all_pages(url, headers, base_params):
    """Busca todas as páginas da API, usando paginação automática."""
    all_items = []
    page = 1

    while True:
        params = {**base_params, "Page": page}
        print(f"📄 Buscando página {page}...")
        data = fetch_page(url, headers, params)
        items = data.get("items", [])
        if not items:
            break

        all_items.extend(items)
        if not data.get("hasNext"):
            break
        page += 1

    print(f"✅ Total de registros obtidos: {len(all_items)}")
    return all_items

def save_debug(data, prefix):
    """Salva JSON bruto para análise posterior."""
    filename = f"debug_{prefix}_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Debug salvo em: {filename}")

def flatten_nested(df, field, sheet_name):
    """Desmembra listas aninhadas em DataFrames separados."""
    rows = []
    for item in df.to_dict(orient="records"):
        base_code = item.get("code")
        for sub in (item.get(field) or []):
            sub["priceTableCode"] = base_code
            rows.append(sub)
    return pd.DataFrame(rows), sheet_name

# === EXECUÇÃO ===
print("🚀 Consultando cabeçalhos de tabelas de preço TOTVS...")

items = get_all_pages(URL, HEADERS, PARAMS)
if not items:
    print("⚠️ Nenhum registro encontrado.")
    sys.exit(0)

save_debug(items, "price_tables_headers")

# === CONVERTE PARA DATAFRAME PRINCIPAL ===
df_main = pd.DataFrame(items)

# === FLAT DOS CAMPOS ANINHADOS ===
nested_fields = {
    "salesOrderClassification": "SalesOrderClassification",
    "personClassification": "PersonClassification",
    "paymentConditions": "PaymentConditions",
    "averagePeriod": "AveragePeriod",
    "averagePeriodQuantity": "AveragePeriodQuantity"
}

flattened_dfs = {}
for field, name in nested_fields.items():
    df_flat, sheet = flatten_nested(df_main, field, name)
    if not df_flat.empty:
        flattened_dfs[sheet] = df_flat

# === RENOMEIA COLUNAS PRINCIPAIS ===
df_main.rename(columns={
    "code": "Codigo",
    "description": "Descricao",
    "codeName": "NomeCodigo",
    "type": "Tipo",
    "maxChangeFilterDate": "DataUltimaAlteracao",
    "startDate": "DataInicio",
    "endDate": "DataFim",
    "variationPercentage": "VariacaoPercentual",
    "variationValue": "VariacaoValor"
}, inplace=True)

# === EXPORTA PARA EXCEL ===
excel_file = f"price_tables_headers_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_main.to_excel(writer, index=False, sheet_name="Headers")
    for sheet, df_flat in flattened_dfs.items():
        df_flat.to_excel(writer, index=False, sheet_name=sheet)

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📊 Total de cabeçalhos: {len(df_main)}")
for name, df_flat in flattened_dfs.items():
    print(f"📄 {name}: {len(df_flat)} registros")
