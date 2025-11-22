import requests
import pandas as pd
from datetime import datetime, timezone
import json
import sys
import os

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/hours/search"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === FILTROS ===
FILTERS_PAYLOAD = {
    "branchs": [5],
    "datemin": "2025-09-01T00:00:00Z",
    "datemax": "2025-09-30T23:59:59Z",
    # "operations": [1, 2],
    # "sellers": [100],
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_sales_details = []
all_summaries = []

print("🚀 Iniciando consulta de Vendas por Hora (Detalhada + DEBUG)...")

while True:
    payload = {
        "branchs": FILTERS_PAYLOAD.get("branchs", []),
        "datemin": FILTERS_PAYLOAD.get("datemin"),
        "datemax": FILTERS_PAYLOAD.get("datemax"),
        "page": page,
        "pageSize": page_size
    }

    # Filtros opcionais
    if 'operations' in FILTERS_PAYLOAD:
        payload['operations'] = FILTERS_PAYLOAD['operations']
    if 'sellers' in FILTERS_PAYLOAD:
        payload['sellers'] = FILTERS_PAYLOAD['sellers']

    print(f"\n⏰ Consultando página {page} de vendas detalhadas…")
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
    debug_file = f"debug_response_sales_hour_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: EXIBIR ESTRUTURA ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    # === DEBUG: EXIBIR AMOSTRA ===
    print("🧩 Amostra do conteúdo (primeiros 1200 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1200])
    print("-" * 60)

    # === PROCESSAMENTO DE DADOS ===
    classification_items = data.get("dataRow", [])
    items_to_check = classification_items

    # Resumo por página
    summary = {
        "InvoiceQuantity": data.get("invoiceQuantity"),
        "InvoiceValue": data.get("invoiceValue"),
        "ItemQuantity": data.get("itemQuantity"),
        "Page": page
    }
    all_summaries.append(summary)

    if not items_to_check:
        print("⚠️ Nenhuma venda encontrada nesta página.")
        break

    for item in items_to_check:
        all_sales_details.append({
            "DataHoraVenda": item.get("saledatetime_hour"),
            "Qtd": item.get("invoice_qty"),
            "ValorLiquido": item.get("invoice_value"),
        })

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages") or data.get("pages") or None
    if total_pages:
        print(f"📖 Página {page}/{total_pages}")
        if page >= total_pages:
            print("✅ Todas as páginas foram processadas.")
            break
    elif len(items_to_check) < page_size:
        print("✅ Última página (parcialmente preenchida).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_sales_detail = pd.DataFrame(all_sales_details)
df_summary = pd.DataFrame(all_summaries).drop_duplicates(subset=["InvoiceValue"])

print("-" * 40)

if df_sales_detail.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    start_date = FILTERS_PAYLOAD["datemin"].split("T")[0]
    end_date = FILTERS_PAYLOAD["datemax"].split("T")[0]
    excel_file = f"vendas_por_hora_debug_{start_date}_a_{end_date}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_sales_detail.to_excel(writer, sheet_name="VendasPorHora", index=False)

            if not df_summary.empty:
                df_summary.head(1).drop(columns=["Page"]).to_excel(
                    writer, sheet_name="ResumoGeral", index=False
                )

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros de vendas por hora: {len(df_sales_detail)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
