import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/accounts-receivable/v2/invoices-print/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🧾 Consultando impressões de faturas...")

# === REQUEST BODY ===
payload = {
    "filter": {
        "change": {
            "startDate": "2024-10-01T00:00:00Z",
            "endDate": "2025-12-31T23:59:59Z"
        },
        "branchCodeList": [2],
        "customerCodeList": [575],
        "receivableCodeList": [2731],
        "installmentCodeList": [1],
        #"invoiceType": "Aberta",
    },
    "order": "dueDate",
    "page": 1,
    "pageSize": 100
}

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=120)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão com a API: {e}")
    sys.exit(1)

print(f"📡 Status HTTP: {response.status_code}")
if response.status_code != 200:
    print("❌ Erro na resposta da API:")
    print(response.text)
    sys.exit(1)

# === TRATAMENTO DO JSON ===
try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA DEBUG ===
debug_file = f"debug_invoices_print_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum registro encontrado.")
    sys.exit(0)

# === LISTAS ===
records = []
payers = []
beneficiaries = []

for item in items:
    records.append({
        "dueDate": item.get("dueDate"),
        "issueDate": item.get("issueDate"),
        "paymentPlace": item.get("paymentPlace"),
        "beneficiaryAgency": item.get("beneficiaryAgency"),
        "ourNumber": item.get("ourNumber"),
        "installmentValue": item.get("installmentValue"),
        "portfolioNumber": item.get("portfolioNumber"),
        "documentNumber": item.get("documentNumber"),
        "documentSpecies": item.get("documentSpecies"),
        "accept": item.get("accept"),
        "processingDate": item.get("processingDate"),
        "currencySpecies": item.get("currencySpecies"),
        "instruction": item.get("instruction"),
        "nameBeneficiary": item.get("nameBeneficiary"),
        "barcode": item.get("barcode"),
        "bankNumber": item.get("bankNumber"),
        "guarantorName": item.get("guarantorName"),
        "guarantorCpfCnpj": item.get("guarantorCpfCnpj")
    })

    payer = item.get("payer")
    if payer:
        payers.append({
            "payerCode": payer.get("code"),
            "payerCpfCnpj": payer.get("cpfCnpjNumber"),
            "payerName": payer.get("name"),
            "address": payer.get("address"),
            "addressNumber": payer.get("addressNumber"),
            "neighborhood": payer.get("neighborhood"),
            "cityName": payer.get("cityName"),
            "stateAbbreviation": payer.get("stateAbbreviation"),
            "cep": payer.get("cep")
        })

    beneficiary = item.get("beneficiary")
    if beneficiary:
        beneficiaries.append({
            "beneficiaryCode": beneficiary.get("code"),
            "beneficiaryCpfCnpj": beneficiary.get("cpfCnpjNumber"),
            "beneficiaryName": beneficiary.get("name"),
            "address": beneficiary.get("address"),
            "addressNumber": beneficiary.get("addressNumber"),
            "neighborhood": beneficiary.get("neighborhood"),
            "cityName": beneficiary.get("cityName"),
            "stateAbbreviation": beneficiary.get("stateAbbreviation"),
            "cep": beneficiary.get("cep")
        })

# === CONVERTE PARA DATAFRAMES ===
df_main = pd.DataFrame(records)
df_payers = pd.DataFrame(payers)
df_beneficiaries = pd.DataFrame(beneficiaries)

# === EXPORTA PARA EXCEL ===
excel_file = f"invoices_print_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_main.to_excel(writer, index=False, sheet_name="Faturas")
    if not df_payers.empty:
        df_payers.to_excel(writer, index=False, sheet_name="Pagadores")
    if not df_beneficiaries.empty:
        df_beneficiaries.to_excel(writer, index=False, sheet_name="Beneficiarios")

print(f"✅ Relatório gerado com sucesso: {excel_file}")
