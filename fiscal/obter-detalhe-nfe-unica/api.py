import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time # Adicionado para consistência

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    """Garante que o retorno seja sempre uma lista."""
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoices/item-detail-search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PARAMS = {
    "BranchCode": 5,    # Empresa (exemplo)
    "InvoiceDate": "2025-11-01T00:00:00Z",
    "InvoiceSequence": 41048,   # Número da fatura
    "Expand": "barcodes,invoiceItemsProduct,invoiceItemTax" 
}

print("🚀 Consultando itens da fatura (item-detail-search)...")

# === REQUISIÇÃO ===
try:
    response = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=60)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na requisição: {e}")
    sys.exit(1)

# === SALVA DEBUG ===
debug_file = f"debug_item_detail_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === TRATAMENTO DOS DADOS ===
items_data = data.get("items", [])

# Listas para as 5 estruturas de dados
invoice_items = []
products = []
taxes = []
referenced_invoices = []
transactions = []

for item in items_data:
    item_sequence = item.get("sequence")
    
    invoice_items.append({
        "invoiceSequence": data.get("invoiceSequence"),
        "itemSequence": item_sequence,
        "code": item.get("code"),
        "name": item.get("name"),
        "ncm": item.get("ncm"),
        "cfop": item.get("cfop"),
        "measureUnit": item.get("measureUnit"),
        "quantity": item.get("quantity"),
        "grossValue": item.get("grossValue"),
        "discountValue": item.get("discountValue"),
        "netValue": item.get("netValue"),
        "unitGrossValue": item.get("unitGrossValue"),
        "unitDiscountValue": item.get("unitDiscountValue"),
        "unitNetValue": item.get("unitNetValue"),
        "additionalValue": item.get("additionalValue"),
        "freightValue": item.get("freightValue"),
        "insuranceValue": item.get("insuranceValue"),
        # Códigos de barra como string (lógica mantida)
        "barcodes": ", ".join(safe_list([b.get("barcode") for b in item.get("barcodes", [])]))
    })

    for prod in safe_list(item.get("invoiceItemsProduct")):
        product_code = prod.get("productCode")
        
        products.append({
            "itemSequence": item_sequence,
            "productCode": product_code,
            "productName": prod.get("productName"),
            "dealerCode": prod.get("dealerCode"),
            "quantity": prod.get("quantity"),
            "unitGrossValue": prod.get("unitGrossValue"),
            "unitDiscountValue": prod.get("unitDiscountValue"),
            "unitNetValue": prod.get("unitNetValue"),
            "grossValue": prod.get("grossValue"),
            "discountValue": prod.get("discountValue"),
            "netValue": prod.get("netValue"),
        })

        # 3. Faturas Referenciadas (referencedInvoices)
        for ref_inv in safe_list(prod.get("referencedInvoices")):
            referenced_invoices.append({
                "itemSequence": item_sequence,
                "productCode": product_code, # Chave composta para rastreamento
                "accessKey": ref_inv.get("accessKey"),
                "satSerialCode": ref_inv.get("satSerialCode"),
                "issueDate": ref_inv.get("issueDate"),
                "invoiceSequenceItem": ref_inv.get("invoiceSequenceItem"),
                "invoiceCode": ref_inv.get("invoiceCode"),
                "invoiceSerialCode": ref_inv.get("invoiceSerialCode"),
                "unitNetValue": ref_inv.get("unitNetValue"),
                "quantity": ref_inv.get("quantity"),
                "cfop": ref_inv.get("cfop"),
                "branchCode": ref_inv.get("branchCode"),
                "branchCnpj": ref_inv.get("branchCnpj"),
                "terminalCode": ref_inv.get("terminalCode"),
            })

        # 4. Transações (transactions)
        for tx in safe_list(prod.get("transactions")):
            sales_order = tx.get("salesOrder", {})
            transactions.append({
                "itemSequence": item_sequence,
                "productCode": product_code,
                "branchCode": tx.get("branchCode"),
                "transactionDate": tx.get("transactionDate"),
                "transactionCode": tx.get("transactionCode"),
                "quantity": tx.get("quantity"),
                "so_branchCode": sales_order.get("branchCode"),
                "so_orderCode": sales_order.get("orderCode"),
                "so_orderId": sales_order.get("orderId"),
                "so_customerOrderCode": sales_order.get("customerOrderCode"),
            })


    # 5. Impostos (invoiceItemTax)
    for tax in safe_list(item.get("invoiceItemTax")):
        taxes.append({
            "itemSequence": item_sequence,
            "taxCode": tax.get("code"),
            "taxName": tax.get("name"),
            "cst": tax.get("cst"), # NOVO CAMPO
            "taxPercentage": tax.get("taxPercentage"),
            "calculationBasisPercentage": tax.get("calculationBasisPercentage"), # NOVO CAMPO
            "calculationBasisDiscountPercentage": tax.get("calculationBasisDiscountPercentage"), # NOVO CAMPO
            "calculationBasisValue": tax.get("calculationBasisValue"),
            "freeValue": tax.get("freeValue"), # NOVO CAMPO
            "otherValue": tax.get("otherValue"), # NOVO CAMPO
            "taxValue": tax.get("taxValue"),
            "benefitCode": tax.get("benefitCode"), # NOVO CAMPO
            "unencumberedValue": tax.get("unencumberedValue"), # NOVO CAMPO
            "unencumberedReason": tax.get("unencumberedReason"), # NOVO CAMPO
            "deferredBaseValue": tax.get("deferredBaseValue"), # NOVO CAMPO
        })

print(f"📦 Total de itens principais processados: {len(invoice_items)}")

# === CONVERTE PARA DATAFRAMES ===
dfs = {
    "Itens_NF": pd.DataFrame(invoice_items),
    "Produtos_Item": pd.DataFrame(products),
    "Impostos": pd.DataFrame(taxes),
    "NFs_Referenciadas": pd.DataFrame(referenced_invoices),
    "Transacoes_Prod": pd.DataFrame(transactions)
}

# === EXPORTA PARA EXCEL ===
excel_file = f"invoice_items_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    for sheet_name, df in dfs.items():
        if not df.empty:
            df.to_excel(writer, index=False, sheet_name=sheet_name)

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📊 Abas exportadas: {', '.join(dfs.keys())}")