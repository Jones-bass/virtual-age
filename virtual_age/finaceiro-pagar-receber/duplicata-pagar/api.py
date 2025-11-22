import os
import sys
import json
import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Any

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from auth.config import TOKEN
except ImportError:
    TOKEN = "YOUR_FALLBACK_TOKEN_HERE"
    print("⚠️ Aviso: TOKEN não encontrado, usando fallback.")

# === CONFIGURAÇÕES ===
BASE_URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/accounts-payable/v2"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === LOG SIMPLES ===
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# === MONTA PAYLOAD ===
def make_payload(
    page: int = 1,
    page_size: int = 100,
    branch_codes: List[int] = [2],
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Any]:

    return {
        "filter": {
            "change": {
                "startDate": "2024-10-01T00:00:00Z",
                "endDate": "2025-10-31T23:59:59Z",
            },
            "branchCodeList": [5],
            "duplicateCodeList": [5],
            "supplierCodeList": [3297],
            "bearerCodeList": [1020]
        },

    }   

# === COLETA COM PAGINAÇÃO ===
def fetch_all_duplicates(start_date: str,
                         end_date: str,
                         branch_codes: List[int] = [2]) -> List[Dict[str, Any]]:
    """Busca todas as duplicatas com paginação."""
    all_items = []
    page = 1
    page_size = 100

    log(f"🔎 Iniciando busca de Duplicatas ({start_date} → {end_date}) nas filiais {branch_codes}")

    while True:
        payload = make_payload(page, page_size, branch_codes, start_date, end_date)
        try:
            response = requests.post(f"{BASE_URL}/duplicates/search", headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                log(f"📄 Página {page} sem resultados. Encerrando busca.")
                break

            all_items.extend(items)
            log(f"📄 Página {page} → {len(items)} duplicatas. Total acumulado: {len(all_items)}")

            if not data.get("hasNext", False):
                break

            page += 1
            time.sleep(0.3)

        except requests.RequestException as e:
            log(f"❌ Erro ao buscar página {page}: {e}")
            if 'response' in locals():
                log(f"Detalhes: {response.text}")
            break

    log(f"✅ Total final de duplicatas obtidas: {len(all_items)}")
    return all_items

# === PROCESSAMENTO DE DADOS ===
def process_duplicates(items: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    """Converte os itens em DataFrames (principal + despesas)."""
    df_main = []
    df_expenses = []

    for item in items:
        df_main.append({
            "maxChangeFilterDate": item.get("maxChangeFilterDate"),
            "branchCode": item.get("branchCode"),
            "duplicateCode": item.get("duplicateCode"),
            "supplierCode": item.get("supplierCode"),
            "supplierCpfCnpj": item.get("supplierCpfCnpj"),
            "installmentCode": item.get("installmentCode"),
            "bearerCode": item.get("bearerCode"),
            "entryDate": item.get("entryDate"),
            "issueDate": item.get("issueDate"),
            "dueDate": item.get("dueDate"),
            "settlementDate": item.get("settlementDate"),
            "arrivalDate": item.get("arrivalDate"),
            "status": item.get("status"),
            "duplicateValue": item.get("duplicateValue"),
            "feesValue": item.get("feesValue"),
            "discountValue": item.get("discountValue"),
            "paidValue": item.get("paidValue"),
            "inclusionType": item.get("inclusionType"),
            "userInclusionCode": item.get("userInclusionCode"),
            "userInclusionName": item.get("userInclusionName"),
        })

        for exp in item.get("expense", []):
            df_expenses.append({
                "duplicateCode": item.get("duplicateCode"),
                "expenseCode": exp.get("expenseCode"),
                "expenseName": exp.get("expenseName"),
                "costCenterCode": exp.get("costCenterCode"),
                "proratedPercentage": exp.get("proratedPercentage"),
                "proratedValue": exp.get("proratedValue"),
            })

    return {
        "Duplicates": pd.DataFrame(df_main),
        "Expenses": pd.DataFrame(df_expenses)
    }

# === EXECUÇÃO ===
if __name__ == "__main__":
    START_DATE = "2025-10-01T00:00:00Z"
    END_DATE = "2025-11-02T23:59:59Z"
    BRANCH_CODES = [2]

    duplicates = fetch_all_duplicates(START_DATE, END_DATE, BRANCH_CODES)

    debug_file = f"debug_duplicates_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(duplicates, f, ensure_ascii=False, indent=2)
    log(f"💾 JSON bruto salvo: {debug_file}")

    if not duplicates:
        log("⚠️ Nenhuma duplicata encontrada.")
        sys.exit(0)

    dfs = process_duplicates(duplicates)

    excel_file = f"duplicates_export_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        for name, df in dfs.items():
            if not df.empty:
                df.to_excel(writer, index=False, sheet_name=name)

    log(f"✅ Exportação concluída com sucesso: {excel_file}")
