import requests
import pandas as pd
from datetime import datetime
import json
import sys

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/accounts-payable/v2/duplicates/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === CORPO DA REQUISIÇÃO ===
payload_base = {
    "filter": {
        "change": {
            "startDate": "2025-12-01T00:00:00Z",
            "endDate": "2025-12-12T23:59:59Z"
        },
        "branchCodeList": [5],
        "duplicateCodeList": [16082024],
        "supplierCodeList": [866],
        "bearerCodeList": [1020],

        # "startExpiredDate": "...",
        # "endExpiredDate": "...",
        # "startSettlementDate": "...",
        # "endSettlementDate": "...",
        "inclusionTypeList": [1],  # se necessário: ["Manual"]
        # "startArrivalDate": "...",
        # "endArrivalDate": "...",
    },
    "order": "issueDate desc"
}

# === PAGINAÇÃO ===
page = 1   # se o endpoint for 0-based, altere para 0
page_size = 100
all_items = []
pagination_summary = []

print("🚀 Iniciando consulta de Duplicatas (Accounts Payable)...")
print(f"📦 Payload base enviado:\n{json.dumps(payload_base, indent=2, ensure_ascii=False)}")
print("-" * 60)

# === LOOP DE PAGINAÇÃO ===
while True:
    # monta payload com paginação
    payload = dict(payload_base)
    payload["page"] = page
    payload["pageSize"] = page_size

    print(f"\n📄 Consultando página {page}…")

    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na conexão: {e}")
        sys.exit(1)

    print(f"📡 Status HTTP: {response.status_code}")

    if response.status_code != 200:
        print("❌ Erro na resposta da API:")
        print(response.text)

        error_file = f"error_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"Status: {response.status_code}\n")
            f.write(response.text)
        print(f"💾 Log de erro salvo em: {error_file}")
        sys.exit(1)

    # === TRATAMENTO DO JSON ===
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        sys.exit(1)

    # === SALVA DEBUG JSON (POR PÁGINA, NA RAIZ) ===
    debug_file = f"debug_duplicates_page_{page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Debug salvo em: {debug_file}")

    # === INSPEÇÃO DE CHAVES ===
    print("\n🔍 Estrutura principal da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tamanho = len(value) if isinstance(value, (list, dict)) else "-"
        print(f"   - {key} ({tipo}) tamanho: {tamanho}")
    print("-" * 60)

    # === RESUMO DE PAGINAÇÃO ===
    pagination_summary.append({
        "page": page,
        "count": data.get("count"),
        "totalItems": data.get("totalItems"),
        "totalPages": data.get("totalPages"),
        "hasNext": data.get("hasNext"),
    })

    items = data.get("items", []) or []
    if not items:
        print("⚠️ Nenhum item retornado nesta página.")
        break

    all_items.extend(items)

    total_pages = data.get("totalPages")
    has_next = data.get("hasNext", False)

    print(f"📖 Página {page}/{total_pages if total_pages is not None else '?'} | items nesta página: {len(items)}")

    # condições de parada
    if total_pages and page >= total_pages:
        print("✅ Todas as páginas foram processadas (totalPages).")
        break
    if not has_next or len(items) < page_size:
        print("✅ Última página (hasNext=False ou retornou menos que pageSize).")
        break

    page += 1

# === ESTRUTURAÇÃO DOS DADOS (FLATTEN expense) ===
rows = []
for it in all_items:
    base = {
        "maxChangeFilterDate": it.get("maxChangeFilterDate"),
        "branchCode": it.get("branchCode"),
        "duplicateCode": it.get("duplicateCode"),
        "supplierCode": it.get("supplierCode"),
        "supplierCpfCnpj": it.get("supplierCpfCnpj"),
        "installmentCode": it.get("installmentCode"),
        "bearerCode": it.get("bearerCode"),
        "entryDate": it.get("entryDate"),
        "issueDate": it.get("issueDate"),
        "dueDate": it.get("dueDate"),
        "settlementDate": it.get("settlementDate"),
        "arrivalDate": it.get("arrivalDate"),
        "status": it.get("status"),
        "duplicateValue": it.get("duplicateValue"),
        "feesValue": it.get("feesValue"),
        "discountValue": it.get("discountValue"),
        "paidValue": it.get("paidValue"),
        "inclusionType": it.get("inclusionType"),
        "userInclusionCode": it.get("userInclusionCode"),
        "userInclusionName": it.get("userInclusionName"),
    }

    expenses = it.get("expense") or []
    if expenses:
        for e in expenses:
            rows.append({
                **base,
                "expenseCode": e.get("expenseCode"),
                "expenseName": e.get("expenseName"),
                "costCenterCode": e.get("costCenterCode"),
                "proratedPercentage": e.get("proratedPercentage"),
                "proratedValue": e.get("proratedValue"),
            })
    else:
        rows.append({
            **base,
            "expenseCode": None,
            "expenseName": None,
            "costCenterCode": None,
            "proratedPercentage": None,
            "proratedValue": None,
        })

df_data = pd.DataFrame(rows)
df_pages = pd.DataFrame(pagination_summary).drop_duplicates(subset=["page"])

print("-" * 60)
if df_data.empty:
    print("⚠️ Nenhum dado encontrado em 'items'.")
else:
    print(f"✅ {len(df_data)} registros estruturados (flatten).")

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"accounts_payable_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        if not df_data.empty:
            df_data.to_excel(writer, index=False, sheet_name="Duplicatas")
        else:
            pd.DataFrame([{"Aviso": "Nenhum dado retornado da API"}]).to_excel(
                writer, index=False, sheet_name="Duplicatas"
            )

        df_pages.to_excel(writer, index=False, sheet_name="Paginacao")

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")

# === JSON CONSOLIDADO NA RAIZ (PADRÃO) ===
json_file = f"accounts_payable_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
try:
    consolidated = {
        "generatedAt": datetime.now().isoformat(),
        "endpoint": URL,
        "requestBase": payload_base,
        "pagination": pagination_summary,
        "count": int(len(df_data)),
        "data": df_data.to_dict(orient="records"),
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2, default=str)

    print(f"🧾 JSON consolidado salvo: {json_file}")
except Exception as e:
    print(f"❌ Erro ao gerar JSON consolidado: {e}")

print("🏁 Execução finalizada com sucesso.")
