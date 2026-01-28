
import requests
from datetime import datetime, timezone
import pandas as pd
import json

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Configurações de API
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sales-order/v2/orders/search"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Variáveis de controle
page = 1
page_size = 200  # Número de itens por página
all_items = []

# Loop de requisições
while True:
    payload = {
        "filter": {
      
            "startOrderDate": "2025-10-01T00:00:00Z",
            "endOrderDate": "2025-10-31T23:59:59Z",
            "orderCodeList": [3075],  # Remover filtro de código de pedido específico
            "branchCodeList": [3],  # Ajustar conforme sua filial
        },
        "page": page,
        "pageSize": page_size
    }

    resp = requests.post(URL, headers=HEADERS, json=payload)
    print(f"Página {page} | Status: {resp.status_code}")

    # Verificação de resposta da API
    if resp.status_code != 200:
        print(f"Erro na requisição: {resp.text}")
        break

    data = resp.json()

    # Salvando JSON para debug
    debug_file = f"debug_orders_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON salvo em: {debug_file}")

    orders = data.get("items", [])
    if not orders:
        print("⚠️ Nenhum pedido encontrado nesta página.")
        break

    # Processar pedidos encontrados
    for order in orders:
        status = order.get("statusOrder")
        
        # Garantir que o campo invoices seja uma lista
        invoices = order.get("invoices", [])
        if invoices is None:  # Caso não exista, defina como lista vazia
            invoices = []

        for invoice in invoices:
            all_items.append({
                "Filial": order.get("branchCode"),
                "Pedido": order.get("orderCode"),
                "OrderID": order.get("orderId"),
                "CustomerOrderCode": order.get("customerOrderCode"),
                "DataPedido": order.get("orderDate"),
                "StatusPedido": status,
                "Quantidade": order.get("quantity"),
                "ValorBruto": order.get("grossValue"),
                "ValorLiquido": order.get("netValue"),
                "ValorFrete": order.get("freightValue"),
                "NomeTransportadora": order.get("shippingCompanyName"),
                "TotalPedido": order.get("totalAmountOrder"),
                "Experience": order.get("experienceType"),
                "InvoiceAccessKey": invoice.get("accessKey"),
                "InvoiceCode": invoice.get("code"),
                "InvoiceSerial": invoice.get("serial"),
                "InvoiceStatus": invoice.get("status"),
                "InvoiceTotalValue": invoice.get("totalValue"),
                "InvoiceShippingValue": invoice.get("shippingValue"),
                "InvoiceTransactionDate": invoice.get("transactionDate"),
                "InvoiceTransactionCode": invoice.get("transactionCode"),
                "InvoiceElectronicStatus": invoice.get("electronic", {}).get("electronicInvoiceStatus"),
            })

    # Verificação de próxima página
    if not data.get("hasNext", False):
        print("✅ Paginação finalizada.")
        break

    page += 1

# Exportação para Excel
df = pd.DataFrame(all_items)
if df.empty:
    print("⚠️ Nenhum registro encontrado.")
else:
    # Conversão de datas e valores
    df["DataPedido"] = pd.to_datetime(df["DataPedido"], errors="coerce")
    df["InvoiceTransactionDate"] = pd.to_datetime(df["InvoiceTransactionDate"], errors="coerce")
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
    df["ValorBruto"] = pd.to_numeric(df["ValorBruto"], errors="coerce")
    df["ValorLiquido"] = pd.to_numeric(df["ValorLiquido"], errors="coerce")
    df["ValorFrete"] = pd.to_numeric(df["ValorFrete"], errors="coerce")
    df["TotalPedido"] = pd.to_numeric(df["TotalPedido"], errors="coerce")
    df["InvoiceTotalValue"] = pd.to_numeric(df["InvoiceTotalValue"], errors="coerce")
    df["InvoiceShippingValue"] = pd.to_numeric(df["InvoiceShippingValue"], errors="coerce")

    # Exportação para o arquivo Excel
    excel_file = "relatorio_totvs_com_invoices.xlsx"
    df.to_excel(excel_file, index=False, sheet_name="Relatorio")
    print(f"✅ Relatório gerado com sucesso: {excel_file} ({len(df)} registros)")
