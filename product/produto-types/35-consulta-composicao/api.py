import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    """Garante que o valor seja sempre uma lista."""
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/compositions"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === FUNÇÃO PRINCIPAL DE PAGINAÇÃO ===
def get_all_compositions():
    todos_itens = []
    page = 1
    page_size = 100

    while True:
        print(f"🔎 Consultando página {page}...")

        payload = {
            "startChangeDate": "2025-01-01T00:00:00Z",
            "endChangeDate": "2025-09-30T23:59:59Z",
        }

        try:
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=90)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            break

        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            break

        data = response.json()
        items = safe_list(data.get("items"))

        if not items:
            print("⚠️ Nenhum item encontrado nesta página.")
            break

        todos_itens.extend(items)

        if not data.get("hasNext", False):
            break

        page += 1
        time.sleep(0.3)

    return todos_itens

# === EXECUTA COLETA ===
print("🚀 Consultando TODAS as composições de produtos TOTVS...")
itens = get_all_compositions()

if not itens:
    print("⚠️ Nenhum dado retornado pela API.")
    sys.exit(0)

# === SALVA DEBUG COMPLETO ===
debug_file = f"debug_compositions_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
composicoes = []
fibras = []

for c in itens:
    composicoes.append({
        "compositionCode": c.get("code"),
        "compositionDescription": c.get("description"),
        "maxChangeFilterDate": c.get("maxChangeFilterDate")
    })

    for f in safe_list(c.get("fibers")):
        fibras.append({
            "compositionCode": c.get("code"),
            "compositionDescription": c.get("description"),
            "fiberCode": f.get("code"),
            "fiberDescription": f.get("description"),
            "fiberPercentage": f.get("percentage")
        })

# === CONVERTE PARA DATAFRAMES ===
df_composicoes = pd.DataFrame(composicoes)
df_fibras = pd.DataFrame(fibras)

# === EXPORTA PARA EXCEL NA PASTA RAIZ ===
excel_file = os.path.join(os.getcwd(), f"compositions_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_composicoes.to_excel(writer, index=False, sheet_name="Composicoes")
    df_fibras.to_excel(writer, index=False, sheet_name="Fibras")

print(f"✅ Relatório completo gerado com sucesso: {excel_file}")
print(f"📊 Total de composições: {len(df_composicoes)}")
print(f"🧵 Total de fibras: {len(df_fibras)}")
