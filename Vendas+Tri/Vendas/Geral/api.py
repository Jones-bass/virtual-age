import json
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import os

# =====================================================
# CONFIGURAÇÕES
# =====================================================

load_dotenv()
TOKEN = os.getenv("TOKEN")

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoices/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# =====================================================
# LOG
# =====================================================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# =====================================================
# PAYLOAD
# =====================================================

def make_payload(page: int = 1, pageSize: int = 100) -> Dict[str, Any]:
    return {
        "filter": {
            "branchCodeList": [3, 5, 7],
            "origin": "All",
            "eletronicInvoiceStatusList": ["Authorized"],
            "startIssueDate": "2026-02-01T00:00:00Z",
            "endIssueDate": "2026-02-28T23:59:59Z"
        },
        "page": page,
        "pageSize": pageSize,
        "order": "invoiceCode",
        "expand": "eletronic,person,shippingCompany,items,salesOrder,payments"
    }

# =====================================================
# BUSCA PAGINADA
# =====================================================

def fetch_all_invoices() -> List[Dict[str, Any]]:
    all_items = []
    page = 1
    page_size = 100

    log("🚀 Iniciando ETL Fiscal Completo...")

    while True:
        payload = make_payload(page, page_size)

        try:
            log(f"   - Buscando página {page}...")
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])

            if not items:
                break

            all_items.extend(items)

            if len(items) < page_size:
                break

            page += 1

        except requests.RequestException as e:
            log(f"❌ Erro na requisição: {e}")
            break

    log(f"✅ Total de notas encontradas: {len(all_items)}")
    return all_items

# =====================================================
# PROCESSAMENTO
# =====================================================

def process_all(items: List[Dict[str, Any]]):

    eletronic_list = []
    person_list = []
    shipping_list = []
    items_list = []
    sales_list = []
    payments_list = []

    for nf in items:

        invoice_code = nf.get("invoiceCode")
        empresa = nf.get("branchCode")

        # ================= ELETRONIC =================
        eletronic = nf.get("eletronic", {}) or {}
        eletronic_list.append({
            "invoiceCode": invoice_code,
            "Empresa": empresa,
            "AccessKey": eletronic.get("accessKey"),
            "ElectronicStatus": eletronic.get("electronicInvoiceStatus"),
            "Receipt": eletronic.get("receipt"),
            "ReceivementDate": eletronic.get("receivementDate"),
        })

        # ================= PERSON =================
        person = nf.get("person", {}) or {}
        person_list.append({
            "invoiceCode": invoice_code,
            "Empresa": empresa,
            "PersonCode": person.get("personCode"),
            "PersonName": person.get("personName"),
            "CpfCnpj": person.get("personCpfCnpj"),
            "City": person.get("city"),
            "State": person.get("stateAbbreviation"),
        })

        # ================= SHIPPING =================
        shipping = nf.get("shippingCompany", {}) or {}
        shipping_list.append({
            "invoiceCode": invoice_code,
            "Empresa": empresa,
            "ShippingCompanyName": shipping.get("shippingCompanyName"),
            "CpfCnpj": shipping.get("cpfCnpj"),
            "FreightValue": shipping.get("freightValue"),
            "City": shipping.get("cityName"),
            "State": shipping.get("stateAbbreviation"),
        })

        # ================= ITEMS =================
        for item in nf.get("items", []) or []:
            items_list.append({
                "invoiceCode": invoice_code,
                "Empresa": empresa,
                "Sequence": item.get("sequence"),
                "ProductCode": item.get("code"),
                "ProductName": item.get("name"),
                "Quantity": item.get("quantity"),
                "UnitNetValue": item.get("unitNetValue"),
                "NetValue": item.get("netValue"),
            })

        # ================= SALES ORDER =================
        for so in nf.get("salesOrder", []) or []:
            sales_list.append({
                "invoiceCode": invoice_code,
                "Empresa": empresa,
                "OrderCode": so.get("orderCode"),
                "OrderId": so.get("orderId"),
                "CustomerOrderCode": so.get("customerOrderCode"),
            })

        # ================= PAYMENTS =================
        for pg in nf.get("payments", []) or []:
            card = pg.get("cardInformation", {}) or {}
            payments_list.append({
                "invoiceCode": invoice_code,
                "Empresa": empresa,
                "PaymentValue": pg.get("paymentValue"),
                "Installment": pg.get("installment"),
                "DocumentType": pg.get("documentType"),
                "CardFlag": card.get("cardFlag"),
                "AuthorizationCode": card.get("authorizationCode"),
                "NSU": card.get("nsu"),
            })

    return (
        pd.DataFrame(eletronic_list),
        pd.DataFrame(person_list),
        pd.DataFrame(shipping_list),
        pd.DataFrame(items_list),
        pd.DataFrame(sales_list),
        pd.DataFrame(payments_list),
    )

# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":

    invoices = fetch_all_invoices()

    debug_file = f"debug_full_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(invoices, f, ensure_ascii=False, indent=2)

    dfs = process_all(invoices)

    excel_file = f"fiscal_full_etl_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        sheet_names = [
            "Eletronic",
            "Person",
            "Shipping",
            "Items",
            "SalesOrder",
            "Payments"
        ]

        for df, name in zip(dfs, sheet_names):
            df.to_excel(writer, index=False, sheet_name=name)

    log(f"✅ ETL Completo gerado: {excel_file}")