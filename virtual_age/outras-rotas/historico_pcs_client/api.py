import requests
import pandas as pd
import json
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN 

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/seller-panel/seller/customer-purchased-products"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

page = 1
page_size = 100
all_sales_items = []

print("🚀 Iniciando consulta de Histórico de Compras Detalhado (Item a Item) + DEBUG...")

while True:
    payload = {
        "branchCodes": [2],
        "startDate": "2025-01-01T00:00:00Z",
        "endDate": "2025-10-30T23:59:59Z",
        "customerCode": 575,
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n🛒 Consultando página {page} de itens vendidos…")

    resp = requests.post(URL, headers=headers, json=payload)
    print(f"📡 Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === DEBUG: SALVAR RESPOSTA JSON ===
    debug_file = f"debug_response_sales_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: ESTRUTURA ===
    print("🔍 Estrutura da resposta JSON:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else 1
        print(f"   - {key}: {tipo} ({tam})")

    print("🧩 Amostra JSON (primeiros 1000 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    print("-" * 60)

    # Extração dos itens
    items_list = data.get("items", [])

    if not items_list:
        if page == 1:
            print("⚠️ Nenhum item encontrado para os filtros aplicados.")
        else:
            print("✅ Paginação concluída ✔ (não há mais dados).")
        break

    for item in items_list:
        all_sales_items.append({
            "Filial": item.get("branchCode"),
            "SequenciaNota": item.get("invoiceSequence"),
            "DataCompra": item.get("purchaseDate"),
            "NumeroNota": item.get("invoiceNumber"),
            "CodCliente": item.get("customerCode"),
            "CPF_CNPJ": item.get("customerCpfCnpj"),
            "CodVendedor": item.get("sellerCode"),
            "CodProduto": item.get("productCode"),
            "DescricaoProduto": item.get("productDescription"),
            "CodCor": item.get("colorCode"),
            "DescricaoCor": item.get("colorDescription"),
            "CodTamanho": item.get("sizeCode"),
            "DescricaoTamanho": item.get("sizeDescription"),
            "CodGrupo": item.get("groupCode"),
            "NomeReferencia": item.get("referenceName"),
            "Quantidade": item.get("quantity"),
            "ValorBruto": item.get("totalGrossValue"),
            "ValorLiquido": item.get("totalNetValue"),
        })

    # Paginação
    if len(items_list) < page_size:
        print("✅ Última página! (menos itens que o pageSize)")
        break

    page += 1


# === EXPORTAÇÃO ===
df_details = pd.DataFrame(all_sales_items)

print("-" * 30)

if df_details.empty:
    print("⚠️ Nenhum dado exportado.")
else:
    excel_file = f"historico_compras_detalhe.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_details.to_excel(writer, sheet_name="HistoricoComprasItem", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"📊 Total de registros exportados: {len(df_details)}")
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")
