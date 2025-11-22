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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/fiscal-movement/search"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 1000
all_movements = []
all_summaries = []

print("🚀 Iniciando consulta Fiscal Movement (Analytics FULL)…")

while True:

    # === PAYLOAD COMPLETO (traz tudo) ===
    payload = {
        "filter": {
            "branchCodeList": [5],  
            
            # === INTERVALO DE DATAS ===
            "startMovementDate": "2025-10-01T00:00:00Z",
            "endMovementDate": "2025-10-30T23:59:59Z",
        },
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n📄 Consultando página {page}…")
    resp = requests.post(URL, headers=headers, json=payload)
    print(f"📡 Status HTTP: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro:", resp.text)
        break

    try:
        data = resp.json()
    except:
        print("❌ Erro ao interpretar JSON da resposta.")
        break

    # === DEBUG: salvar resposta ===
    debug_file = f"debug_fiscal_movement_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Armazenado: {debug_file}")

    # === VERIFICA DADOS ===
    items = data.get("items", [])

    # Caso venha somente o objeto fictício zerado
    if len(items) == 1 and items[0].get("branchCode") == 0:
        print("⚠️ A API retornou objeto placeholder (dados zerados).")
        print("   Isso indica que o filtro não trouxe dados reais.")
        break

    if not items:
        print("⚠️ Nenhum movimento real encontrado nesta página.")
        break

    # === CARREGAR MOVIMENTOS ===
    for item in items:
        # Verificando se a operação 151 está presente
        if item.get("operationCode") == "151":
            print(f"⚠️ Operação 151 encontrada: {item}")  # Log para verificar a operação

        all_movements.append({
            "Filial": item.get("branchCode"),
            "Produto": item.get("productCode"),
            "Pessoa": item.get("personCode"),
            "Representante": item.get("representativeCode"),
            "DataMovimento": item.get("movementDate"),
            "Operacao": item.get("operationCode"),
            "ModeloOperacao": item.get("operationModel"),
            "Estoque": item.get("stockCode"),
            "Comprador": item.get("buyerCode"),
            "Vendedor": item.get("sellerCode"),
            "ValorBruto": item.get("grossValue"),
            "ValorDesconto": item.get("discountValue"),
            "ValorLiquido": item.get("netValue"),
            "Quantidade": item.get("quantity"),
        })

    # === RESUMO ===
    summary = {
        "Page": page,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
        "HasNext": data.get("hasNext")
    }
    all_summaries.append(summary)

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages", 0)
    has_next = data.get("hasNext", False)

    if not has_next or page >= total_pages:
        print("✅ Fim da paginação.")
        break

    page += 1

# === EXPORTAÇÃO DOS RESULTADOS ===
df_movements = pd.DataFrame(all_movements)
df_summary = pd.DataFrame(all_summaries)

print("\n" + "-" * 50)

if df_movements.empty:
    print("⚠️ Nenhum dado encontrado para salvar no Excel.")
else:
    excel_file = "movimentos_fiscais_full.xlsx"
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df_movements.to_excel(writer, sheet_name="Movimentos", index=False)
        df_summary.to_excel(writer, sheet_name="Resumo", index=False)

    print(f"📊 Arquivo gerado com sucesso: {excel_file}")
    print(f"Total de registros coletados: {len(df_movements)}")
