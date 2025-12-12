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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sales-order/v2/orders/search"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

page = 1
page_size = 200
all_items = []

while True:
    payload = {
        "filter": {
            "change": {
                "startDate": "2025-01-01T00:00:00Z",
                "endDate": "2025-10-26T23:59:59Z",
            },
            "branchCodeList": [2],  # ajuste conforme sua filial
        },
    }

    resp = requests.post(URL, headers=HEADERS, json=payload)
    print(f"\n📄 Página {page} | Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    data = resp.json()

    # === DEBUG: salvar JSON cru para inspeção se necessário ===
    debug_file = f"debug_orders_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON cru salvo em: {debug_file}")

    orders = data.get("items", [])
    if not orders:
        print("⚠️ Nenhum pedido encontrado nesta página.")
        break

    for order in orders:
        # ⚡ Status original direto da API
        status = order.get("statusOrder")

        all_items.append({
            "Filial": order.get("branchCode"),
            "Pedido": order.get("orderCode"),
            "OrderID": order.get("orderId"),
            "CustomerOrderCode": order.get("customerOrderCode"),
            "DataInsercao": order.get("insertDate"),
            "DataPedido": order.get("orderDate"),
            "DataChegada": order.get("arrivalDate"),
            "DataUltimaAlteracao": order.get("maxChangeFilterDate"),
            "Cliente": order.get("customerName"),
            "CPF_CNPJ_Cliente": order.get("customerCpfCnpj"),
            "CodigoCliente": order.get("customerCode"),
            "Representante": order.get("representativeName"),
            "CodigoRepresentante": order.get("representativeCode"),
            "Operacao": order.get("operationName"),
            "CodigoOperacao": order.get("operationCode"),
            "CondicaoPagamento": order.get("paymentConditionName"),
            "CodigoCondicaoPagamento": order.get("paymentConditionCode"),
            "Quantidade": order.get("quantity"),
            "ValorBruto": order.get("grossValue"),
            "ValorDesconto": order.get("discountValue"),
            "ValorLiquido": order.get("netValue"),
            "ValorFrete": order.get("freightValue"),
            "TipoFrete": order.get("freightType"),
            "CodigoTransportadora": order.get("shippingCompanyCode"),
            "NomeTransportadora": order.get("shippingCompanyName"),
            "StatusPedido": status,  # ✅ pega exatamente da API
            "TotalPedido": order.get("totalAmountOrder"),
            "Experiencia": order.get("experienceType"),
            "TemTransacaoPDV": order.get("hasPdvTransaction"),
            "TemFinanceiroProcessado": order.get("hasFinancialProcessed"),
            "CodigoIntegracao": order.get("integrationCode"),
            "CodigoGuia": order.get("guideCode"),
            "CPF_CNPJGuia": order.get("guideCpfCnpj"),
            "VendedorCodigo": order.get("sellerCode"),
            "VendedorCPF_CNPJ": order.get("sellerCpfCnpj"),
        })

    if not data.get("hasNext", False):
        print("✅ Paginação finalizada.")
        break

    page += 1

# === EXPORTAÇÃO PARA EXCEL COM TRATAMENTO DE DATAS E VALORES ===
df = pd.DataFrame(all_items)

if df.empty:
    print("⚠️ Nenhum registro encontrado no período.")
else:
    # Conversão de datas apenas para colunas de data
    date_cols = ["DataInsercao", "DataPedido", "DataChegada", "DataUltimaAlteracao"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # Conversão de valores apenas para colunas numéricas
    numeric_cols = ["Quantidade", "ValorBruto", "ValorDesconto", "ValorLiquido",
                    "ValorFrete", "TotalPedido"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # StatusPedido permanece string, exatamente como vem da API
    excel_file = "relatorio_totvs.xlsx"
    df.to_excel(excel_file, index=False, sheet_name="Relatorio")

    print(f"✅ Relatório gerado com sucesso: {excel_file} ({len(df)} registros)")
