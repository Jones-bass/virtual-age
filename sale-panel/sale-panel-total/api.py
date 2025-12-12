import requests
import pandas as pd
from datetime import datetime, timezone
import json
import sys
import os

# Caminho para importar o token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/totals/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_sales_current = []
all_sales_last_year = []

print("🚀 Iniciando consulta de Vendas (Comparativo Anual)...")

while True:
    payload = {
        "branchs": [5],                       # Filial
        "datemin": "2025-09-01T00:00:00Z",    # Início do período
        "datemax": "2025-09-30T23:59:59Z",  
        "page": page,
        "pageSize": page_size
    }

    print(f"\n⏰ Consultando página {page}...")
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
    debug_file = f"debug_response_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: estrutura da resposta ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    # === DEBUG: mostra parte do JSON ===
    print("🧩 Amostra do conteúdo (primeiros 1200 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1200])
    print("-" * 50)

    # === Extração dos dados ===
    current_items = data.get("dataRow", [])
    last_year_items = data.get("dataRowLastYear", [])

    if not current_items and page == 1:
        print("⚠️ Nenhuma venda encontrada para o período atual e filtros aplicados.")
        break
    if not current_items and page > 1:
        print("✅ Paginação concluída (não há mais dados).")
        break

    # ANO ATUAL
    for item in current_items:
        all_sales_current.append({
            "Ano": "Atual",
            "Qtd": item.get("invoice_qty"),
            "ValorLiquido": item.get("invoice_value"),
            "QtdItens": item.get("itens_qty"),
            "TicketMedio": item.get("tm"),
            "PcaAtendida": item.get("pa"),
            "PMPV": item.get("pmpv"),
        })

    # ANO PASSADO
    for item in last_year_items:
        all_sales_last_year.append({
            "Ano": "Anterior",
            "Invoice_Qty": item.get("invoice_qty"),
            "Invoice_Value": item.get("invoice_value"),
            "Itens_Qty": item.get("itens_qty"),
            "TM": item.get("tm"),
            "PA": item.get("pa"),
            "PMPV": item.get("pmpv"),
        })

    # === PAGINAÇÃO: verifica se há mais páginas ===
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

# --- EXPORTAÇÃO ---
df_current = pd.DataFrame(all_sales_current)
df_last_year = pd.DataFrame(all_sales_last_year)

print("-" * 30)
if df_current.empty and df_last_year.empty:
    print("⚠️ Nenhum dado de vendas para exportar.")
else:
    excel_file = f"vendas_comparativo.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            if not df_current.empty:
                df_current.to_excel(writer, sheet_name="AnoAtual", index=False)
            if not df_last_year.empty:
                df_last_year.to_excel(writer, sheet_name="AnoAnterior", index=False)
        print(f"✅ Relatório gerado: {excel_file}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
