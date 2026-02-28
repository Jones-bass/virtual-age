import json
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES GERAIS ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoices/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === UTIL ===
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def make_payload(page: int = 1, pageSize: int = 100) -> Dict[str, Any]:
    return {
        "filter": {
            "branchCodeList": [3],
            "operationCodeList": [
                111,112,151,551,504,505,701,702,5100,5101,5102,5103,
                5104,5105,5106,5111,5551,5953,5961,5962,5965,5974,
                5975,7101,119,120,121,171,172,173,182,183,221,
                222,1201,1202,1204,1207,1208,2200,2116
            ],
            "origin": "All",
            "eletronicInvoiceStatusList": ["Authorized"],
            "startIssueDate": "2026-02-01T00:00:00Z",
            "endIssueDate": "2026-02-26T23:59:59Z"
        },
        "page": page,
        "pageSize": pageSize,
        "order": "invoiceCode",
        "expand": "eletronic, shippingCompany, person"
    }


def fetch_all_invoices() -> List[Dict[str, Any]]:
    all_items = []
    page = 1
    page_size = 100

    log("🔎 Iniciando busca paginada...")

    while True:
        payload = make_payload(page, page_size)

        try:
            log(f"   - Buscando página {page}")
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
            log(f"❌ Erro na página {page}: {e}")
            break

    log(f"✅ Total de notas retornadas: {len(all_items)}")
    return all_items


def process_invoice(nf: Dict[str, Any]) -> Dict[str, Any]:
    eletronic = nf.get("eletronic", {}) or {}
    shipping = nf.get("shippingCompany", {}) or {}
    person = nf.get("person", {}) or {}

    return {
        # Dados principais
        "Empresa": nf.get("branchCode"),
        "Emissao": nf.get("issueDate"),
        "Transacao": nf.get("transactionCode"),
        "Operacao": nf.get("operationCode"),
        "Codigo_Cliente": nf.get("personCode"),
        "Cliente": nf.get("personName"),
        "Valor_Total": nf.get("totalValue"),

        # === PERSON ===
        "Cidade": person.get("city"),
        "UF": person.get("stateAbbreviation"),
        "CEP": person.get("cep"),
        "Telefone": person.get("foneNumber"),
        "CPF_CNPJ": person.get("personCpfCnpj"),

        # === SHIPPING COMPANY ===
        "Transportadora": shipping.get("shippingCompanyName"),
        "Frete": shipping.get("freightValue"),

        # === ELETRONIC ===
        "Serie": nf.get("serialCode"),
        "Chave_NFe": eletronic.get("accessKey"),
        "Status_NFe": eletronic.get("electronicInvoiceStatus"),
    }


# === EXECUÇÃO ===
if __name__ == "__main__":

    log("🚀 Iniciando consulta...")
    items = fetch_all_invoices()

    debug_file = f"debug_fiscal_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    log(f"💾 Debug salvo: {debug_file}")

    invoices = [process_invoice(nf) for nf in items]

    df = pd.DataFrame(invoices)

    excel_file = f"fiscal_eletronic_shipping_person_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="NotasFiscais")

    log(f"✅ Excel gerado: {excel_file}")
    log(f"📊 Total exportado: {len(invoices)}")