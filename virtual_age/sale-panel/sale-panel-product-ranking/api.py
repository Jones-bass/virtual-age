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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sale-panel/v2/product-classifications/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

page = 1
page_size = 100
all_classification_details = []
all_summaries = []

print("🚀 Iniciando consulta de Vendas por Classificação de Produto (com DEBUG)...")

while True:
    payload = {
        "branchs": [5],
        "datemin": "2025-09-01T00:00:00Z",
        "datemax": "2025-09-30T23:59:59Z",
        "classification_type_code": "102", 
        "page": page,
        "pageSize": page_size
    }

    print(f"\n🏷️ Consultando página {page} de classificações…")
    resp = requests.post(URL, headers=headers, json=payload)
    print(f"📡 Status HTTP: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === DEBUG: salvar JSON cru ===
    debug_file = f"debug_response_classification_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: estrutura de chaves ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else 1
        print(f"   - {key}: {tipo} ({tam})")

    # === DEBUG: amostra parcial do JSON ===
    print("🧩 Amostra (primeiros 1000 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    print("-" * 60)

    # === Processa dados ===
    classification_items = data.get("dataRow", [])
    if page == 1:
        all_summaries.append({
            "InvoiceQuantity": data.get("invoiceQuantity"),
            "InvoiceValue": data.get("invoiceValue"),
            "ItemQuantity": data.get("itemQuantity"),
        })

    if not classification_items:
        print("⚠️ Nenhum dado encontrado nesta página.")
        break

    for item in classification_items:
        all_classification_details.append({
            "CodigoClassificacao": item.get("classification_code"),
            "NomeClassificacao": item.get("classification_name"),
            "ValorVenda": item.get("invoice_value"),
            "QuantidadeItens": item.get("item_quantity")
        })

    # === Controle de Paginação ===
    total_pages = data.get("totalPages") or data.get("pages") or None
    if total_pages:
        print(f"📖 Página {page}/{total_pages}")
        if page >= total_pages:
            print("✅ Todas as páginas foram processadas.")
            break
    elif len(classification_items) < page_size:
        print("✅ Última página (parcial).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_details = pd.DataFrame(all_classification_details)
df_summary = pd.DataFrame(all_summaries)

print("=" * 50)

if df_details.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    excel_file = f"vendas_classificacao.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_details.to_excel(writer, sheet_name="DetalhesClassificacao", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoGeral", index=False)

        print(f"✅ Relatório Excel gerado: {excel_file}")
        print(f"📊 Total de registros: {len(df_details)}")
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")
