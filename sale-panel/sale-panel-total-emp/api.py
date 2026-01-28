import requests
import pandas as pd
import json

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/totals-branch/search"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

page = 1
page_size = 500
all_sales_current = []
all_sales_last_year = []
all_summaries = []

SUMMARY_FIELDS = ["invoice_qty", "invoice_value", "itens_qty", "tm", "pa", "pmpv"]

print("🚀 Iniciando consulta de Vendas (Comparativo por Filial com Debug)...")

while True:
    payload = {
        "branchs": [5],                      
        "datemin": "2025-09-01T00:00:00Z",
        "datemax": "2025-09-30T23:59:59Z",
        "page": page,
        "pageSize": page_size
    }

    print(f"\n⏰ Consultando página {page} de dados comparativos (filial)…")
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

    # === DEBUG: salvar resposta bruta ===
    debug_file = f"debug_response_branch_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: estrutura geral ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    # === DEBUG: amostra do conteúdo ===
    print("🧩 Amostra do conteúdo (primeiros 1200 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1200])
    print("-" * 60)

    # === Extração ===
    current_items = data.get("dataRow", [])
    last_year_items = data.get("dataRowLastYear", [])

    # --- Resumos (somente primeira página para evitar duplicação) ---
    if page == 1:
        total_current = {"Ano": "Atual - TOTAL"}
        total_current.update({k: data.get("total", {}).get(k) for k in SUMMARY_FIELDS})
        all_summaries.append(total_current)

        total_last_year = {"Ano": "Anterior - TOTAL"}
        total_last_year.update({k: data.get("totalLastYear", {}).get(k) for k in SUMMARY_FIELDS})
        all_summaries.append(total_last_year)

    # --- Interrupção se não houver dados ---
    if not current_items and not last_year_items:
        print("✅ Paginação concluída (não há mais dados).")
        break

    # --- ANO ATUAL ---
    for item in current_items:
        all_sales_current.append({
            "Ano": "Atual",
            "CodeLoja": item.get("branch_code"),
            "Loja": item.get("branch_name"),
            "Qtd": item.get("invoice_qty"),
            "ValorLiquido": item.get("invoice_value"),
            "QtdItens": item.get("itens_qty"),
            "TicketMedio": item.get("tm"),
            "PecasAtend": item.get("pa"),
            "PMPV": item.get("pmpv"),
        })

    # --- ANO ANTERIOR ---
    for item in last_year_items:
        all_sales_last_year.append({
            "Ano": "Anterior",
            "CodeLoja": item.get("branch_code"),
            "Loja": item.get("branch_name"),
            "Qtd": item.get("invoice_qty"),
            "ValorLiquido": item.get("invoice_value"),
            "QtdItens": item.get("itens_qty"),
            "TicketMedio": item.get("tm"),
            "PecasAtend": item.get("pa"),
            "PMPV": item.get("pmpv"),
        })

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages") or data.get("pages") or None
    if total_pages:
        print(f"📖 Página {page}/{total_pages}")
        if page >= total_pages:
            print("✅ Todas as páginas foram processadas.")
            break
    elif len(current_items) < page_size:
        print("✅ Última página (parcialmente preenchida).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_current = pd.DataFrame(all_sales_current)
df_last_year = pd.DataFrame(all_sales_last_year)
df_summary = pd.DataFrame(all_summaries)

print("-" * 40)
if df_current.empty and df_last_year.empty:
    print("⚠️ Nenhum dado de vendas para exportar.")
else:
    excel_file = f"vendas_comparativo_filial.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            if not df_current.empty:
                df_current.to_excel(writer, sheet_name="AnoAtual", index=False)
            if not df_last_year.empty:
                df_last_year.to_excel(writer, sheet_name="AnoAnterior", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="Resumo_Geral", index=False)
        print(f"✅ Relatório gerado: {excel_file}")
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")
