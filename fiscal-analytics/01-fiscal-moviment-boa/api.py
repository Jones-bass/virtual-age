import requests
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/fiscal-movement/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1  # Primeira página
page_size = 1000  # Tamanho da página
all_movements = []  # Para armazenar todos os dados
all_summaries = []  # Para armazenar os resumos das páginas

print("🚀 Iniciando consulta de Movimentos Fiscais (Analytics + DEBUG)...")

while True:
    payload = {
          "filter": {
            "branchCodeList": [5], 
            
            "startMovementDate": "2026-01-01T00:00:00Z",
            "endMovementDate": "2026-01-13T23:59:59Z",
        },
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n📄 Consultando página {page + 1} de movimentos fiscais…")
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
    debug_file = f"debug_response_fiscal_movement_page_{page + 1}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === PROCESSAMENTO DE DADOS ===
    items = data.get("items", [])
    if not items:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    for item in items:
        all_movements.append({
            "BranchCode": item.get("branchCode"),
            "ProductCode": item.get("productCode"),
            "PersonCode": item.get("personCode"),
            "RepresentativeCode": item.get("representativeCode"),
            "MovementDate": item.get("movementDate"),
            "OperationCode": item.get("operationCode"),
            "OperationModel": item.get("operationModel"),
            "StockCode": item.get("stockCode"),
            "BuyerCode": item.get("buyerCode"),
            "SellerCode": item.get("sellerCode"),
            "GrossValue": item.get("grossValue"),
            "DiscountValue": item.get("discountValue"),
            "NetValue": item.get("netValue"),
            "Quantity": item.get("quantity"),
        })

    # Resumo da página
    summary = {
        "Page": page + 1,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
    }
    all_summaries.append(summary)

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages")
    has_next = data.get("hasNext", False)

    if total_pages and page >= total_pages - 1:
        print("✅ Todas as páginas foram processadas.")
        break
    elif not has_next or len(items) < page_size:
        print("✅ Última página (sem próxima).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_movements = pd.DataFrame(all_movements)
df_summary = pd.DataFrame(all_summaries).drop_duplicates(subset=["Page"])

print("-" * 40)

if df_movements.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"movimentos_fiscais_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_movements.to_excel(writer, sheet_name="Movimentos Fiscais", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoPáginas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros exportados: {len(df_movements)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
