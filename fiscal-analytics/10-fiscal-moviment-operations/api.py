import requests
import pandas as pd
import json
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/operation-fiscal-movement/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 100
all_operations = []
all_summaries = []

print("🚀 Iniciando consulta de Operações (Analytics + DEBUG)...")

while True:
    payload = {
        "filter": {
            "branchCodeList": [3, 5, 7, 9],
            "startMovementDate": "2026-06-01T00:00:00Z",
            "endMovementDate": "2026-06-21T00:00:00Z",
        },
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n📄 Consultando página {page} de operações…")
    resp = requests.post(URL, headers=headers, json=payload)
    print(f"📡 Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === DEBUG: SALVAR RESPOSTA ===
    debug_file = f"debug_response_operations_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: EXIBIR ESTRUTURA ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    print("🧩 Amostra (primeiros 1000 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    print("-" * 60)

    # === PROCESSAMENTO DE DADOS ===
    items = data.get("items", [])
    if not items:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    for item in items:
        all_operations.append({
            "Codigo": item.get("code"),
            "Nome": item.get("name"),
            "Modelo": item.get("model"),
        })

    summary = {
        "Page": page,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
    }
    all_summaries.append(summary)

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages")
    has_next = data.get("hasNext", False)

    if total_pages and page >= total_pages:
        print("✅ Todas as páginas foram processadas.")
        break
    elif not has_next or len(items) < page_size:
        print("✅ Última página (sem próxima).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_operations = pd.DataFrame(all_operations)
df_summary = pd.DataFrame(all_summaries).drop_duplicates(subset=["Page"])

print("-" * 40)

if df_operations.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"operacoes_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_operations.to_excel(writer, sheet_name="Operacoes", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoPaginas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros exportados: {len(df_operations)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")