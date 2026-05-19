import requests
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import time

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/fiscal-movement/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === FILTROS ===
branch_codes = [2]  # Se a API aceitar todos com [0], você pode testar [0]
start_date = "2026-01-01T00:00:00Z"
end_date = "2026-01-31T23:59:59Z"

# === PAGINAÇÃO ===
page = 1
page_size = 1000

all_items = []
all_summaries = []

print("🚀 Iniciando consulta de Movimentos Fiscais...")

while True:
    payload = {
        "filter": {
            "branchCodeList": branch_codes,
            "startMovementDate": start_date,
            "endMovementDate": end_date
        },
        "page": page,
        "pageSize": page_size
    }

    print(f"\n📄 Consultando página {page}...")

    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        break

    print(f"📡 Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:")
        print(resp.text)
        break

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        print(resp.text)
        break

    # === DEBUG: SALVAR RESPOSTA COMPLETA ===
    debug_file = f"debug_response_fiscal_movement_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Resposta salva em: {debug_file}")

    items = data.get("items", [])

    summary = {
        "Page": page,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
        "HasNext": data.get("hasNext"),
        "ItemsNaPagina": len(items)
    }

    all_summaries.append(summary)

    if not items:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    # Aqui traz TODOS os campos retornados pela API
    all_items.extend(items)

    print(f"✅ Registros coletados nesta página: {len(items)}")
    print(f"📦 Total acumulado: {len(all_items)}")

    has_next = data.get("hasNext", False)
    total_pages = data.get("totalPages")

    # Regra principal de parada
    if not has_next:
        print("✅ Última página encontrada pelo hasNext.")
        break

    # Regra extra de segurança
    if total_pages is not None and total_pages > 0 and page >= total_pages - 1:
        print("✅ Todas as páginas processadas pelo totalPages.")
        break

    page += 1

    # Pequena pausa para não bater forte na API
    time.sleep(0.2)

# === EXPORTAÇÃO ===
print("-" * 40)

if not all_items:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    df_movements = pd.json_normalize(all_items)
    df_summary = pd.DataFrame(all_summaries)

    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"movimentos_fiscais_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_movements.to_excel(writer, sheet_name="Movimentos Fiscais", index=False)
            df_summary.to_excel(writer, sheet_name="ResumoPaginas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros exportados: {len(df_movements)}")
        print(f"Total de colunas exportadas: {len(df_movements.columns)}")

        print("\n📌 Colunas retornadas pela API:")
        for col in df_movements.columns:
            print(f"- {col}")

    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")