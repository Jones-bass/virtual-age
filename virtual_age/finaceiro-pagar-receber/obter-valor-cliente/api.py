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
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/accounts-receivable/v2/customer-financial-balance/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando saldos financeiros de clientes...")

# === REQUEST BODY ===
payload = {
    "filter": {
        "change": {
            "startDate": "2025-10-01T00:00:00Z",
            "endDate": "2025-12-31T23:59:59Z",
            "branchCodeList": [2],
            "inLimit": True,
            "inOpenInvoice": True,
            "inRefundCredit": True,
            "inAdvanceAmount": True,
            "inDofni": True,
            "inDofniCheck": True,
            "inTransactionOut": True,
            "inConsigned": True,
        },
        "customerCodeList": [575],
    },
    "option": {
        "branchCodeList": [2],
        "isLimit": True,
        "isOpenInvoice": True,
        "isRefundCredit": True,
        "isAdvanceAmount": True,
        "isDofni": True,
        "isDofniCheck": True,
        "isTransactionOut": True,
        "isConsigned": True,
        "isInvoiceBehindSchedule": True,
        "dateInvoiceBehindSchedule": "2025-12-31T23:59:59Z",
    },
}

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=90)
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
debug_file = f"debug_customer_financial_balance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA DADOS ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum saldo financeiro retornado pela API.")
    sys.exit(0)

clientes = []
valores = []

for item in items:
    clientes.append({
        "code": item.get("code"),
        "name": item.get("name"),
        "cpfCnpj": item.get("cpfCnpj"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

    for val in safe_list(item.get("values")):
        valores.append({
            "customerCode": item.get("code"),
            "branchCode": val.get("branchCode"),
            "limitValue": val.get("limitValue"),
            "openInvoiceValue": val.get("openInvoiceValue"),
            "refundCreditValue": val.get("refundCreditValue"),
            "advanceAmountValue": val.get("advanceAmountValue"),
            "dofniValue": val.get("dofniValue"),
            "dofniCheckValue": val.get("dofniCheckValue"),
            "transactionOutValue": val.get("transactionOutValue"),
            "consignedValue": val.get("consignedValue"),
            "invoicesBehindScheduleValue": val.get("invoicesBehindScheduleValue"),
            "lastChangeLimitDate": val.get("lastChangeLimitDate"),
            "salesOrderAdvanceValue": val.get("salesOrderAdvanceValue")
        })

# === CONVERTE PARA DATAFRAMES ===
df_clientes = pd.DataFrame(clientes)
df_valores = pd.DataFrame(valores)

# === EXPORTA PARA EXCEL ===
excel_file = f"customer_financial_balance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_clientes.to_excel(writer, index=False, sheet_name="Clientes")
    if not df_valores.empty:
        df_valores.to_excel(writer, index=False, sheet_name="Valores")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
