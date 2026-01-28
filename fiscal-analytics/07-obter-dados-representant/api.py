import requests
import pandas as pd
import json
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/representative-fiscal-movement/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 1000

all_reps = []
all_summaries = []

print("🚀 Iniciando consulta de Representantes (Analytics + DEBUG)...")

while True:
    payload = {
        "filter": {
            "branchCodeList": [2],
            "startMovementDate": "2025-11-01T00:00:00Z",
            "endMovementDate": "2025-12-31T23:59:59Z",
        },
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n📄 Consultando página {page} de representantes…")
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
    debug_file = f"debug_response_representatives_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: ESTRUTURA ===
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
        all_reps.append({
            "CodigoRepresentante": item.get("code"),
            "Nome": item.get("name"),
            "CPF/CNPJ": item.get("cpfCnpj"),
            "NomeFantasia": item.get("fantasyName"),
            "Inativo": item.get("isInactive"),
        })

    summary = {
        "Page": page,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
        "HasNext": data.get("hasNext"),
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
df_reps = pd.DataFrame(all_reps)
df_summary = pd.DataFrame(all_summaries).drop_duplicates(subset=["Page"])

print("-" * 40)

if df_reps.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"representantes_lista_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_reps.to_excel(writer, sheet_name="Representantes", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoPaginas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros exportados: {len(df_reps)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
