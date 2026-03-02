import json
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import os

# ==============================
# CONFIGURAÇÕES
# ==============================

load_dotenv()
TOKEN = os.getenv("TOKEN")

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoices/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ==============================
# FUNÇÃO DE LOG
# ==============================

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ==============================
# PAYLOAD
# ==============================

def make_payload(page: int = 1, pageSize: int = 100) -> Dict[str, Any]:
    return {
        "filter": {
            "branchCodeList": [3, 5, 7],
            "operationCodeList": [
                111,112,151,551,504,505,701,702,5100,5101,5102,5103,5104,5105,5106,
                5111,5551,5953,5961,5962,5965,5974,5975,7101,
                119,120,121,171,172,173,182,183,221,222,1201,1202,
                1204,1207,1208,2200,2116
            ],
            "origin": "All",
            "eletronicInvoiceStatusList": ["Authorized"],
            "startIssueDate": "2026-02-01T00:00:00Z",
            "endIssueDate": "2026-02-28T23:59:59Z"
        },
        "page": page,
        "pageSize": pageSize,
        "order": "invoiceCode",
        "expand": "person"
    }

# ==============================
# BUSCA PAGINADA
# ==============================

def fetch_all_invoices() -> List[Dict[str, Any]]:
    all_items = []
    page = 1
    page_size = 100

    log("👤 Iniciando busca de notas fiscais (somente person)...")

    while True:
        payload = make_payload(page, page_size)

        try:
            log(f"   - Buscando página {page}...")
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])

            if not items:
                log("   - Nenhum item retornado. Fim da busca.")
                break

            all_items.extend(items)
            log(f"   - {len(items)} registros retornados. Total acumulado: {len(all_items)}")

            if len(items) < page_size:
                break

            page += 1

        except requests.RequestException as e:
            log(f"❌ Erro na requisição: {e}")
            break

    log(f"✅ Total final de notas encontradas: {len(all_items)}")
    return all_items

# ==============================
# PROCESSA SOMENTE PERSON
# ==============================

def process_person(nf: Dict[str, Any]) -> Dict[str, Any]:
    person = nf.get("person", {}) or {}

    return {
        "Empresa": nf.get("branchCode"),
        "invoiceCode": nf.get("invoiceCode"),
        "Serie": nf.get("serialCode"),
        "IssueDate": nf.get("issueDate"),

        # Dados do Cliente
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
    }

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================

if __name__ == "__main__":
    log("🚀 Iniciando processo...")

    items = fetch_all_invoices()

    # Debug JSON
    debug_file = f"debug_person_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    log(f"💾 Arquivo debug salvo: {debug_file}")

    # Processa dados do cliente
    persons = []
    for nf in items:
        try:
            persons.append(process_person(nf))
        except Exception as e:
            log(f"⚠️ Erro ao processar invoice {nf.get('invoiceCode')}: {e}")

    df_person = pd.DataFrame(persons)

    # Exporta Excel
    excel_file = f"person_invoices_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    df_person.to_excel(excel_file, index=False)

    log(f"✅ Excel gerado com sucesso: {excel_file}")
    log(f"📊 Total de registros exportados: {len(df_person)}")