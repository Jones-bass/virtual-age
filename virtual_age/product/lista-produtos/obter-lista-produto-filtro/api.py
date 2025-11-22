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

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/product-codes/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Iniciando consulta de códigos de produtos alterados...")

# === VARIÁVEIS DE CONTROLE ===
page = 1
page_size = 1000
all_items = []

# === PARÂMETROS DE CONSULTA ===
payload_base = {
    "filter": {
        "change": {
            "startDate": "2025-10-01T00:00:00Z",
            "endDate": "2025-10-31T23:59:59Z",
            "inBranchInfo": True,
            "branchInfoCodeList": [1, 2, 3],  # 🔧 Pode adicionar mais filiais aqui
        },
        "branchInfo": {"branchCode": 1, "isActive": True},
        "classifications": [
            {
                "type": 104,
                "codeList": ["001", "002", "003", "004", "005", "006"]
            }
        ],
    },
    "order": "productCode",
}

# === LOOP DE PAGINAÇÃO ===
while True:
    print(f"📄 Consultando página {page}...")

    payload = payload_base.copy()
    payload["page"] = page
    payload["pageSize"] = page_size

    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na conexão com a API: {e}")
        sys.exit(1)

    # === DEBUG PARCIAL ===
    print(f"📡 Status HTTP: {response.status_code}")
    if page == 1:
        debug_file = f"debug_product_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Debug salvo em: {debug_file}")

    items = data.get("items", [])
    if not items:
        print("⚠️ Nenhum item retornado nesta página.")
        break

    all_items.extend(items)

    # Controle de próxima página
    if not data.get("hasNext", False):
        break

    page += 1
    time.sleep(0.2)

print(f"\n✅ Total de produtos retornados: {len(all_items)}")

# === TRATA OS DADOS ===
if not all_items:
    print("⚠️ Nenhum produto encontrado no intervalo informado.")
    sys.exit(0)

df = pd.DataFrame(all_items)

# === ENRIQUECIMENTO DE DADOS ===
df["maxChangeFilterDate"] = pd.to_datetime(df["maxChangeFilterDate"], errors="coerce")
df["data_consulta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df["mes_referencia"] = "Outubro/2025"
df["origem_dados"] = "TOTVS Moda API - product-codes/search"

# === CÁLCULOS RESUMIDOS ===
df["ano"] = df["maxChangeFilterDate"].dt.year
df["mes"] = df["maxChangeFilterDate"].dt.month
df["dia"] = df["maxChangeFilterDate"].dt.day

# === ESTATÍSTICAS GERAIS ===
total_produtos = len(df)
data_min = df["maxChangeFilterDate"].min()
data_max = df["maxChangeFilterDate"].max()

# === RELATÓRIO DE RESUMO ===
summary_data = {
    "Total de produtos": [total_produtos],
    "Primeira alteração registrada": [data_min],
    "Última alteração registrada": [data_max],
    "Data de consulta": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
}

df_summary = pd.DataFrame(summary_data)

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"product_codes_rich_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="ProductCodes")
    df_summary.to_excel(writer, index=False, sheet_name="Resumo")

print(f"\n✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📊 Total de produtos: {total_produtos}")
print(f"🕒 Alterações entre: {data_min} e {data_max}")
