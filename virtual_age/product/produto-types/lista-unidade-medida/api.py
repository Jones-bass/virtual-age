import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from auth.config import TOKEN

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    """Garante que o valor seja uma lista."""
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/measurement-unit"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando unidades de medida...")

# === PARÂMETROS DE PAGINAÇÃO ===
all_items = []
page = 1
page_size = 100

while True:
    params = {
        "StartChangeDate": "2024-01-01T00:00:00Z",
        "EndChangeDate": "2025-09-30T23:59:59Z",
        "Expand": "additionalVariations",
        }

    try:
        response = requests.get(URL, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        sys.exit(1)

    items = data.get("items", [])
    if not items:
        break

    all_items.extend(items)
    print(f"📄 Página {page} carregada ({len(items)} itens).")

    if not data.get("hasNext", False):
        break

    page += 1
    time.sleep(0.3)

print(f"✅ Total de unidades retornadas: {len(all_items)}")

# === SALVA DEBUG ===
debug_file = f"debug_measurement_unit_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === TRATAMENTO DOS DADOS ===
unidades = []
variacoes_adicionais = []

for item in all_items:
    # === UNIDADES DE MEDIDA ===
    unidades.append({
        "code": item.get("code"),
        "description": item.get("description"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

    # === VARIAÇÕES ADICIONAIS ===
    for var in safe_list(item.get("additionalVariations")):
        variacoes_adicionais.append({
            "unitCode": item.get("code"),
            "code": var.get("code"),
            "description": var.get("description"),
            "isTribXml": var.get("isTribXml")
        })

# === CONVERTE PARA DATAFRAMES ===
df_unidades = pd.DataFrame(unidades)
df_variacoes = pd.DataFrame(variacoes_adicionais)

# === EXPORTA PARA EXCEL ===
excel_file = f"measurement_units_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_unidades.to_excel(writer, index=False, sheet_name="Unidades")
    if not df_variacoes.empty:
        df_variacoes.to_excel(writer, index=False, sheet_name="VariacoesAdicionais")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📦 Unidades: {len(df_unidades)}, Variações: {len(df_variacoes)}")
