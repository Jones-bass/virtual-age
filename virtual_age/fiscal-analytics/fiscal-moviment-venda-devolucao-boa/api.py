import requests
import pandas as pd
import sys
import os
from datetime import datetime
import json

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/branch-sale"
# URL = "https://treino.bhan.com.br:9443/api/totvsmoda/analytics/v2/branch-sale"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

page = 1
page_size = 1000
all_sales = []
pagination_summary = []

# === PARÂMETROS ===
params = {
    # "BranchCnpj": "41791600000445", #Atacado
    # "BranchCnpj": "45877608000218",#CJ
     "BranchCnpj": "45877608000137", #MG
    # "BranchCnpj": "41791600000526",  # ECOM
    "StartDate": "2025-10-01T00:00:00Z",
    "EndDate": "2025-10-31T23:59:59Z",
    "pageSize": page_size
}

print("\n🚀 Iniciando consulta de Branch Sales com DEBUG...\n")

# === LOOP DE PAGINAÇÃO ===
while True:
    print(f"\n📄 Consultando página {page}…")
    
    # Atualiza página atual no params
    params["page"] = page

    resp = requests.get(URL, headers=headers, params=params)
    print(f"📡 Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    # === TENTA DECODIFICAR JSON ===
    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("❌ Erro ao decodificar JSON.")
        break

    # === DEBUG: SALVAR RESPOSTA ===
    debug_file = f"debug_branch_sale_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: MOSTRAR ESTRUTURA ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tamanho = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"  - {key}: {tipo} ({tamanho})")

    # === DEBUG: AMOSTRA PARCIAL DO JSON ===
    print("\n🧩 Amostra dos dados (1000 chars):")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
    print("-" * 80)

    # === PROCESSAR ITENS ===
    items = data.get("items", [])

    if not items:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    for item in items:
        all_sales.append({
            "CNPJ Filial": item.get("branchCnpj"),
            "Sequência NF": item.get("invoiceSequence"),
            "Valor Venda": item.get("SaleValue"),
            "Data Venda": item.get("saleDate"),
            "Hora Venda": item.get("SaleHour"),
            "Status NF": item.get("invoiceStatus"),
            "Tipo Operação": item.get("operationType"),
            "Código Operação": item.get("operationCode"),
        })

    # === RESUMO DE PAGINAÇÃO ===
    pagination_summary.append({
        "page": page,
        "totalItems": data.get("totalItems"),
        "count": data.get("count"),
        "totalPages": data.get("totalPages"),
    })

    total_pages = data.get("totalPages", 1)
    print(f"📖 Página {page}/{total_pages}")

    if page >= total_pages:
        print("✅ Todas as páginas processadas.")
        break

    page += 1

# === EXPORTAÇÃO ===
if all_sales:
    df_sales = pd.DataFrame(all_sales)
    df_pages = pd.DataFrame(pagination_summary)

    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"vendas_query_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_sales.to_excel(writer, sheet_name="Vendas", index=False)
            df_pages.to_excel(writer, sheet_name="Paginacao", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"📦 Total de registros: {len(df_sales)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
else:
    print("⚠️ Nenhum dado para exportar.")
