import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    """Garante que o retorno seja sempre uma lista."""
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/accounts-receivable/v2/documents/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando documentos de contas a receber...")

# === REQUEST BODY ===
payload = {
    "filter": {
        "change": {
            "startDate": "2025-10-01T00:00:00Z",
            "endDate": "2025-12-31T23:59:59Z",
            "inCheck": True
        },
        "branchCodeList": [2],
        "customerCodeList": [575],
        "statusList": [1],
        "hasOpenInvoices": True,
    },
    "page": 1,
    "pageSize": 100,
    "order": "receivableCode"
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
debug_file = f"debug_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum documento retornado pela API.")
    sys.exit(0)

# === TABELAS ===
docs = []
checks = []
invoices = []
commissions = []

for item in items:
    docs.append({
        "branchCode": item.get("branchCode"),
        "customerCode": item.get("customerCode"),
        "customerCpfCnpj": item.get("customerCpfCnpj"),
        "receivableCode": item.get("receivableCode"),
        "installmentCode": item.get("installmentCode"),
        "status": item.get("status"),
        "documentType": item.get("documentType"),
        "billingType": item.get("billingType"),
        "dischargeType": item.get("dischargeType"),
        "chargeType": item.get("chargeType"),
        "expiredDate": item.get("expiredDate"),
        "paymentDate": item.get("paymentDate"),
        "issueDate": item.get("issueDate"),
        "installmentValue": item.get("installmentValue"),
        "paidValue": item.get("paidValue"),
        "netValue": item.get("netValue"),
        "discountValue": item.get("discountValue"),
        "rebateValue": item.get("rebateValue"),
        "interestValue": item.get("interestValue"),
        "barCode": item.get("barCode"),
        "ourNumber": item.get("ourNumber"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

    check = item.get("check")
    if check:
        checks.append({
            "receivableCode": item.get("receivableCode"),
            "checkBand": check.get("checkBand"),
            "bankNumber": check.get("bankNumber"),
            "agencyNumber": check.get("agencyNumber"),
            "checkNumber": check.get("checkNumber"),
            "account": check.get("account"),
            "checkThirdName": check.get("checkThirdName"),
            "reasonForReturnDescription1": check.get("reasonForReturnDescription1"),
            "reasonForReturnDescription2": check.get("reasonForReturnDescription2"),
            "reasonForReturnDescription3": check.get("reasonForReturnDescription3")
        })

    for inv in safe_list(item.get("invoice")):
        invoices.append({
            "receivableCode": item.get("receivableCode"),
            "branchCode": inv.get("branchCode"),
            "invoiceSequence": inv.get("invoiceSequence"),
            "invoiceDate": inv.get("invoiceDate"),
            "invoiceCode": inv.get("invoiceCode")
        })

    for com in safe_list(item.get("commissions")):
        commissions.append({
            "receivableCode": item.get("receivableCode"),
            "commissionedCode": com.get("commissionedCode"),
            "commissionedCpfCnpj": com.get("commissionedCpfCnpj"),
            "typeCode": com.get("typeCode"),
            "typeDescription": com.get("typeDescription"),
            "percentageBilling": com.get("percentageBilling"),
            "valueBilling": com.get("valueBilling"),
            "percentageReceived": com.get("percentageReceived"),
            "valueReceived": com.get("valueReceived"),
            "paymentDateBilling": com.get("paymentDateBilling"),
            "paymentDateReceived": com.get("paymentDateReceived")
        })

# === CONVERTE PARA DATAFRAMES ===
df_docs = pd.DataFrame(docs)
df_checks = pd.DataFrame(checks)
df_invoices = pd.DataFrame(invoices)
df_commissions = pd.DataFrame(commissions)

# === EXPORTA PARA EXCEL ===
excel_file = f"accounts_receivable_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_docs.to_excel(writer, index=False, sheet_name="Documentos")
    if not df_checks.empty:
        df_checks.to_excel(writer, index=False, sheet_name="Cheques")
    if not df_invoices.empty:
        df_invoices.to_excel(writer, index=False, sheet_name="NotasFiscais")
    if not df_commissions.empty:
        df_commissions.to_excel(writer, index=False, sheet_name="Comissoes")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
