import requests
import pandas as pd
import json
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://treino.bhan.com.br:9443/api/totvsmoda/analytics/v2/branch-fiscal-movement/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_partners = []
all_summaries = []

print("🚀 Iniciando consulta de Parceiros / Filiais (Analytics + DEBUG)...")

while True:
    payload = {
        "filter": {
            "branchCodeList": [3],
            "startMovementDate": "2025-12-01T00:00:00Z",
            "endMovementDate": "2025-12-30T00:00:00Z",
        },
    }

    print(f"\n📄 Consultando página {page} de parceiros…")
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
    debug_file = f"debug_response_partners_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

 

    # === PROCESSAMENTO DE DADOS ===
    items = data.get("items", [])
    if not items:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    for item in items:
        addr = item.get("address", {}) or {}
        all_partners.append({
            "Codigo": item.get("code"),
            "CNPJ": item.get("cnpj"),
            "Nome": item.get("name"),
            "NomeFantasia": item.get("fantasyName"),
            "Logradouro": addr.get("publicPlace"),
            "Endereco": addr.get("address"),
            "Numero": addr.get("addressNumber"),
            "Bairro": addr.get("neighborhood"),
            "Cidade": addr.get("cityName"),
            "UF": addr.get("stateAbbreviation"),
            "CEP": addr.get("cep"),
            "Pais": addr.get("countryName"),
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
df_partners = pd.DataFrame(all_partners)
df_summary = pd.DataFrame(all_summaries).drop_duplicates(subset=["Page"])

print("-" * 40)

if df_partners.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"parceiros_lista_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_partners.to_excel(writer, sheet_name="Parceiros", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoPaginas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros exportados: {len(df_partners)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
