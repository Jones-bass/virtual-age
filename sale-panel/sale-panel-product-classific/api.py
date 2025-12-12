import requests
import pandas as pd
from datetime import datetime, timezone
import json
import sys
import os

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÃO DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/branch-ranking/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Lista de campos de métricas para mapeamento
DETAIL_FIELDS = [
    "branchCode", "branch_name", "invoice_qty", "invoice_value", "itens_qty",
    "tm", "pa", "pmpv", "cash_value", "pix_value", "credit_value",
    "debit_value", "installment_value", "other_value"
]

# === FILTROS ===
FILTERS_PAYLOAD = {
    "branchs": [5],
    "datemin": "2025-09-01T00:00:00Z",
    "datemax": "2025-09-30T23:59:59Z",
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_sales_details = []
all_summaries = []

print("🚀 Iniciando consulta de Vendas Detalhadas (por Filial e Pagamento + DEBUG)...")

while True:
    # Montando o payload para a requisição POST
    payload = {
        "branchs": FILTERS_PAYLOAD.get("branchs", []),
        "datemin": FILTERS_PAYLOAD.get("datemin"),
        "datemax": FILTERS_PAYLOAD.get("datemax"),
        "page": page,
        "pageSize": page_size
    }

    print(f"\n🏬 Consultando página {page} de detalhes de vendas…")
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

    # === DEBUG: salvar resposta ===
    debug_file = f"debug_response_branch_ranking_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: exibir estrutura ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    # === DEBUG: amostra parcial do conteúdo ===
    print("🧩 Amostra do conteúdo (primeiros 1200 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1200])
    print("-" * 60)

    # === PROCESSAMENTO DE DADOS ===
    detail_items = data.get("dataRow", [])
    items_to_check = detail_items

    # Resumo geral (somente primeira página)
    if page == 1 and data.get("invoiceValue") is not None:
        summary_data = {"Tipo": "TOTAL_GERAL"}
        summary_data.update({
            k.replace('_value', 'Value').replace('_qty', 'Quantity').upper(): data.get(k)
            for k in DETAIL_FIELDS if k not in ["branchCode", "branch_name"]
        })
        all_summaries.append(summary_data)

    if not items_to_check:
        print("⚠️ Nenhum dado encontrado nesta página.")
        break

    # Processa os itens detalhados
    for item in detail_items:
        all_sales_details.append({
            "BranchCode": item.get("branchCode"),
            "BranchName": item.get("branch_name"),
            "FaturaQty": item.get("invoice_qty"),
            "ValorLiquido": item.get("invoice_value"),
            "ItensQty": item.get("itens_qty"),
            "TM": item.get("tm"),
            "PA": item.get("pa"),
            "PMPV": item.get("pmpv"),
            "CashValor": item.get("cash_value"),
            "PixValor": item.get("pix_value"),
            "CreditoValor": item.get("credit_value"),
            "DebitoValor": item.get("debit_value"),
            "ValorParcela": item.get("installment_value"),
            "OutroValor": item.get("other_value"),
        })

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages") or data.get("pages") or None
    if total_pages:
        print(f"📖 Página {page}/{total_pages}")
        if page >= total_pages:
            print("✅ Todas as páginas foram processadas.")
            break
    elif len(detail_items) < page_size:
        print("✅ Última página (parcialmente preenchida).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_details = pd.DataFrame(all_sales_details)
df_summary = pd.DataFrame(all_summaries)

print("-" * 40)

if df_details.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    start_date = FILTERS_PAYLOAD["datemin"].split("T")[0]
    end_date = FILTERS_PAYLOAD["datemax"].split("T")[0]
    excel_file = f"vendas_filial_pagamento_debug_{start_date}_a_{end_date}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_details.to_excel(writer, sheet_name="DetalhesPorFilial", index=False)

            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoGeral", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros detalhados: {len(df_details)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
