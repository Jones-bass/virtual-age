import requests
from datetime import datetime, timezone
import pandas as pd
import json
import sys
import os

# === CONFIGURAÇÕES DE PATH E TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/purchase-order/v2/search"  # 🔁 rota de compra

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 100
all_items = []

while True:
    payload = {
        "filter": {
            "change": {
                "startDate": "2025-09-01T00:00:00Z",
                "endDate": "2025-09-30T00:00:00Z",
            },
            "branchCodeList": [2],  
        },
        "page": page,
        "pageSize": page_size
    }


    resp = requests.post(URL, headers=HEADERS, json=payload)
    print(f"\n📄 Página {page} | Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    data = resp.json()

    # === DEBUG opcional ===
    debug_file = f"debug_purchase_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON cru salvo em: {debug_file}")

    orders = data.get("items", [])
    if not orders:
        print("⚠️ Nenhum pedido encontrado nesta página.")
        break

    for order in orders:
        all_items.append({
            "Filial": order.get("branchCode"),
            "Pedido": order.get("orderCode"),
            "CodigoFornecedor": order.get("supplierCode"),
            "Fornecedor": order.get("supplierName"),
            "CNPJ_Fornec": order.get("supplierCpfCnpj"),
            "CodigoComprador": order.get("buyerCode"),
            "Comprador": order.get("buyerName"),
            "Operacao": order.get("operationName"),
            "CodigoOperacao": order.get("operationCode"),
            "Transportadora": order.get("shippingCompanyName"),
            "CondicaoPagamento": order.get("paymentConditionName"),
            "CodigoCondicaoPagamento": order.get("paymentConditionCode"),
            "TipoPagamento": order.get("paymentType"),
            "Status": order.get("status"),
            "TipoFrete": order.get("freightType"),
            "DataRegistro": order.get("registrationDate"),
            "PrevisaoEntrega": order.get("deliveryForecastDate"),
            "LimiteEntrega": order.get("deliveryDeadlineDate"),
            "DataBasePagamento": order.get("basePaymentDate"),
            "ValorProduto": order.get("productValue"),
            "IPI": order.get("ipiValue"),
            "Quantidade": order.get("quantity"),
            "TotalPedido": order.get("totalAmountOrder")
        })

    if not data.get("hasNext", False):
        print("✅ Paginação finalizada.")
        break

    page += 1

# === EXPORTAÇÃO PARA EXCEL ===
df = pd.DataFrame(all_items)

if df.empty:
    print("⚠️ Nenhum registro encontrado no período.")
else:
    # Conversão de datas
    date_cols = ["DataRegistro", "PrevisaoEntrega", "LimiteEntrega", "DataBasePagamento"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Conversão de valores numéricos
    numeric_cols = ["ValorProduto", "IPI", "Quantidade", "TotalPedido"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    excel_file = "relatorio_compras.xlsx"
    df.to_excel(excel_file, index=False, sheet_name="Relatorio")

    print(f"✅ Relatório gerado com sucesso: {excel_file} ({len(df)} registros)")
