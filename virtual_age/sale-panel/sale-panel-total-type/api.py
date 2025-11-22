import requests
import pandas as pd
from datetime import datetime, timezone
import json
import sys
import os

# Caminho para importar o TOKEN
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/document-types/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_payment_details = []
all_summaries = []

print("🚀 Iniciando consulta de Vendas por Forma de Pagamento (com Debug)...")

while True:
    payload = {
        "branchs": [3],
        "datemin": "2025-09-01T00:00:00Z",
        "datemax": "2025-09-30T23:59:59Z",
        "page": page,
        "pageSize": page_size
    }

    print(f"\n💳 Consultando página {page} de pagamentos…")
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

    # === DEBUG: salvar resposta completa ===
    debug_file = f"debug_response_payment_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: mostrar estrutura da resposta ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    # === DEBUG: amostra parcial do conteúdo ===
    print("🧩 Amostra do conteúdo (primeiros 1200 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1200])
    print("-" * 60)

    # === Extração dos dados ===
    payment_items = data.get("dataRow", [])
    items_to_check = payment_items

    # --- Resumo (primeira página apenas) ---
    if page == 1:
        summary = {
            "invoiceQuantity": data.get("invoiceQuantity"),
            "ValorLiquido": data.get("invoiceValue"),
            "itemQuantity": data.get("itemQuantity"),
        }
        all_summaries.append(summary)

    if not items_to_check:
        print("✅ Paginação concluída (não há mais dados).")
        break

    # --- Processamento dos itens ---
    for item in payment_items:
        all_payment_details.append({
            "TipoDocumentoPagamento": item.get("payment_document_type"),
            "ValorPagamento": item.get("payment_value"),
            "BranchCode_Filtro": item.get("branchs", [0]),
        })

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages") or data.get("pages") or None
    if total_pages:
        print(f"📖 Página {page}/{total_pages}")
        if page >= total_pages:
            print("✅ Todas as páginas foram processadas.")
            break
    elif len(payment_items) < page_size:
        print("✅ Última página (parcialmente preenchida).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_details = pd.DataFrame(all_payment_details)
df_summary = pd.DataFrame(all_summaries)

print("-" * 40)
if df_details.empty:
    print("⚠️ Nenhum dado de pagamento encontrado para exportar.")
else:
    excel_file = f"vendas_por_pagamento.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_details.to_excel(writer, sheet_name="DetalhesPagamento", index=False)
            print(f"Total de registros de pagamento: {len(df_details)}")

            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoGeral", index=False)
                print("Resumo Geral exportado.")

        print(f"✅ Relatório gerado: {excel_file}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
