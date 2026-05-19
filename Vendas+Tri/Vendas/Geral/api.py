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
            # "change": {
            #    "startDate": "2026-04-01T00:00:00.643Z",
            #    "endDate": "2026-04-30T23:59:59.643Z"
            #    },
            "branchCodeList": [3, 5, 7, 9],
            "origin": "All",
            "operationCodeList": [
                111, 112, 151, 551, 504, 505, 701, 702, 5100, 5101, 5102, 5103, 5104, 5105, 5106,
                5108, 5109, 5111, 5551, 5953, 5961, 5962, 5965, 5974, 5975, 7101,
                119, 120, 121, 171, 172, 173, 182, 183, 221, 222, 1201, 1202,
                1204, 1207, 1208, 2200, 2116, 2949
            ],
            "eletronicInvoiceStatusList": ["Authorized"],
            "startIssueDate": "2026-04-01T00:00:00Z",
            "endIssueDate": "2026-04-27T23:59:59Z"
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
# PROCESSAMENTO DE PRODUCTS
# =====================================================
def process_products(nf: Dict[str, Any]) -> List[Dict[str, Any]]:
    processed = []
    items = nf.get("items") or []

    if not items:
        # placeholder quando items é null
        processed.append({
            "Empresa": nf.get("branchCode"),
            "branchCnpj": nf.get("branchCnpj"),
            "invoiceCode": nf.get("invoiceCode"),
            "invoiceSequence": nf.get("invoiceSequence"),
            "SerialCode": nf.get("serialCode"),
            "IssueDate": nf.get("issueDate"),
            "ProductCode": None,
            "ProductName": None,
            "DealerCode": None,
            "Quantity": None,
            "UnitGrossValue": None,
            "UnitDiscountValue": nf.get("discountPercentage"),
            "UnitNetValue": nf.get("totalValue"),
            "GrossValue": nf.get("productValue"),
            "DiscountValue": nf.get("discountPercentage"),
            "NetValue": nf.get("totalValue"),
        })
    else:
        for item in items:
            for product in item.get("products", []):
                processed.append({
                    "Empresa": nf.get("branchCode"),
                    "branchCnpj": nf.get("branchCnpj"),
                    "invoiceCode": nf.get("invoiceCode"),
                    "invoiceSequence": nf.get("invoiceSequence"),
                    "SerialCode": nf.get("serialCode"),
                    "IssueDate": nf.get("issueDate"),
                    "ProductCode": product.get("productCode"),
                    "ProductName": product.get("productName"),
                    "DealerCode": product.get("dealerCode"),
                    "Quantity": product.get("quantity"),
                    "UnitGrossValue": product.get("unitGrossValue"),
                    "UnitDiscountValue": product.get("unitDiscountValue"),
                    "UnitNetValue": product.get("unitNetValue"),
                    "GrossValue": product.get("grossValue"),
                    "DiscountValue": product.get("discountValue"),
                    "NetValue": product.get("netValue"),
                })

    return processed

# =====================================================
# PROCESSAMENTO COMPLETO
# =====================================================
def process_all(items: List[Dict[str, Any]]):
    eletronic_list, person_list, shipping_list = [], [], []
    items_list, sales_list, payments_list = [], [], []
    products_list, taxes_list, barcodes_list = [], [], []
    rate_differential_list, observation_nf_list, referenced_tax_invoice_list = [], [], []

    for nf in items:
        # ELETRONIC
        eletronic = nf.get("eletronic") or {}
        eletronic_list.append({
            "invoiceCode": nf.get("invoiceCode"),
            "Empresa": nf.get("branchCode"),
            "branchCnpj": nf.get("branchCnpj"),
            "invoiceSequence": nf.get("invoiceSequence"),
            "invoiceDate": nf.get("invoiceDate"),
            "operationCode": nf.get("operationCode"),
            "operationType": nf.get("operationType"),
            "operatioName": nf.get("operatioName"),
            "serie": nf.get("serialCode"),
            "exitTime": nf.get("exitTime"),
            "lastchangeDate": nf.get("lastchangeDate"),
            "totalValue": nf.get("totalValue"),
            "discountPercentage": nf.get("discountPercentage"),
            "productValue": nf.get("productValue"),
            "additionalValue": nf.get("additionalValue"),
            "shippingValue": nf.get("shippingValue"),
            "insuranceValue": nf.get("insuranceValue"),
            "ipiValue": nf.get("ipiValue"),
            "baseIcmsValue": nf.get("baseIcmsValue"),
            "icmsValue": nf.get("icmsValue"),
            "icmsSubStValue": nf.get("icmsSubStValue"),
            "terminalCode": nf.get("terminalCode"),
            "sellerCpf": nf.get("sellerCpf"),
            "accessKey": eletronic.get("accessKey"),
            "electronicInvoiceStatus": eletronic.get("electronicInvoiceStatus"),
            "receipt": eletronic.get("receipt"),
            "receivementDate": eletronic.get("receivementDate"),
            "disableProtocol": eletronic.get("disableProtocol"),
            "disableDate": eletronic.get("disableDate")
        })

        # PERSON
        person = nf.get("person") or {}
        person_list.append({
            "Empresa": nf.get("branchCode"),
            "branchCnpj": nf.get("branchCnpj"),
            "invoiceCode": nf.get("invoiceCode"),
            "invoiceSequence": nf.get("invoiceSequence"),
            "Serie": nf.get("serialCode"),
            "IssueDate": nf.get("issueDate"),
            "PersonCode": person.get("personCode"),
            "PersonName": person.get("personName"),
            "PersonType": person.get("personType"),
            "CpfCnpj": person.get("personCpfCnpj"),
            "RG_IE": person.get("rgIe"),
            "Phone": person.get("foneNumber"),
            "Address": person.get("address"),
            "AddressNumber": person.get("addressNumber"),
            "Complement": person.get("complement"),
            "Neighborhood": person.get("neighborhood"),
            "City": person.get("city"),
            "State": person.get("stateAbbreviation"),
            "Cep": person.get("cep"),
        })

        # SHIPPING
        shipping = nf.get("shippingCompany") or {}
        shipping_list.append({
            "invoiceCode": nf.get("invoiceCode"),
            "Empresa": nf.get("branchCode"),
            "branchCnpj": nf.get("branchCnpj"),
            "ShippingCompanyCode": shipping.get("shippingCompanyCode"),
            "ShippingCompanyName": shipping.get("shippingCompanyName"),
            "FreightType": shipping.get("freightType"),
            "FreightValue": shipping.get("freightValue"),
            "CpfCnpj": shipping.get("cpfCnpj"),
            "City": shipping.get("cityName"),
            "State": shipping.get("stateAbbreviation"),
            "Cep": shipping.get("cep"),
            "PlaqueCode": shipping.get("plaqueCode"),
            "GrossWeight": shipping.get("grossWeight"),
            "NetWeight": shipping.get("netWeight"),
            "TrackingCode": shipping.get("trackingCode"),
        })

        # ITEMS
        for item in nf.get("items") or []:
            items_list.append({
                "invoiceCode": nf.get("invoiceCode"),
                "Empresa": nf.get("branchCode"),
                "ProductCode": item.get("code"),
                "ProductName": item.get("name"),
                "NCM": item.get("ncm"),
                "CFOP": item.get("cfop"),
                "MeasureUnit": item.get("measureUnit"),
                "Quantity": item.get("quantity"),
                "UnitGrossValue": item.get("unitGrossValue"),
                "UnitDiscountValue": item.get("unitDiscountValue"),
                "UnitNetValue": item.get("unitNetValue"),
                "GrossValue": item.get("grossValue"),
                "DiscountValue": item.get("discountValue"),
                "NetValue": item.get("netValue"),
                "FreightValue": item.get("freightValue"),
                "InsuranceValue": item.get("insuranceValue"),
                "AdditionalValue": item.get("additionalValue"),
            })

        # SALES ORDER
        for so in nf.get("salesOrder") or []:
            sales_list.append({
                "invoiceCode": nf.get("invoiceCode"),
                "Empresa": nf.get("branchCode"),
                "OrderCode": so.get("orderCode"),
                "OrderId": so.get("orderId"),
                "CustomerOrderCode": so.get("customerOrderCode"),
            })

        # PAYMENTS
        for pg in nf.get("payments") or []:
            card = pg.get("cardInformation") or {}
            payments_list.append({
                "invoiceCode": nf.get("invoiceCode"),
                "Empresa": nf.get("branchCode"),
                "PaymentValue": pg.get("paymentValue"),
                "Installment": pg.get("installment"),
                "DocumentType": pg.get("documentType"),
                "CardFlag": card.get("cardFlag"),
                "AuthorizationCode": card.get("authorizationCode"),
                "NSU": card.get("nsu"),
            })

        # PRODUCTS
        products_list.extend(process_products(nf))

    # Retorna todos os DataFrames
    return (
        pd.DataFrame(eletronic_list),
        pd.DataFrame(person_list),
        pd.DataFrame(shipping_list),
        pd.DataFrame(items_list),
        pd.DataFrame(sales_list),
        pd.DataFrame(payments_list),
        pd.DataFrame(products_list),
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
        sheet_names = ["Eletronic", "Person", "Shipping", "Items", "SalesOrder", "Payments", "Products"]
        for df, name in zip(dfs, sheet_names):
            df.to_excel(writer, index=False, sheet_name=name)

    log(f"✅ ETL Completo gerado: {excel_file}")