import os, sys
import json
import requests
import pandas as pd
from datetime import datetime

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from auth.config import TOKEN

URL_SALES = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/branch-sale"
URL_OPS   = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/operation-fiscal-movement/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def fetch_pages(
    method: str,
    url: str,
    *,
    headers: dict,
    base_params=None,
    base_json=None,
    page_size=500,
    items_key="items",
    debug=False,
    debug_prefix="response"
):
    """Itera páginas e retorna (items, resumo_paginas). Suporta GET (params) e POST (json).
       Se debug=True: salva JSON por página na raiz + mostra estrutura e amostra.
    """
    s = requests.Session()
    s.headers.update(headers)

    items_all, pages = [], []
    page = 1

    while True:
        params = dict(base_params or {})
        payload = dict(base_json or {})

        if method.upper() == "GET":
            params.update({"page": page, "pageSize": page_size})
            r = s.get(url, params=params)
        else:
            payload.update({"page": page, "pageSize": page_size})
            r = s.post(url, json=payload)

        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code} em {url}: {r.text[:500]}")

        data = r.json()

        # === DEBUG: SALVAR JSON + MOSTRAR ESTRUTURA + AMOSTRA (NA RAIZ) ===
        if debug:
            debug_file = f"{debug_prefix}_page_{page}.json"
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"\n💾 Resposta salva em: {debug_file}")
            print("🔍 Estrutura da resposta:")
            for key, value in data.items():
                tipo = type(value).__name__
                tamanho = len(value) if isinstance(value, (list, dict)) else 1
                print(f"  - {key}: {tipo} ({tamanho})")

            print("\n🧩 Amostra (primeiros 1000 chars):")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])
            print("-" * 80)

        items = data.get(items_key, []) or []

        pages.append({
            "page": page,
            "count": data.get("count"),
            "totalItems": data.get("totalItems"),
            "totalPages": data.get("totalPages"),
            "hasNext": data.get("hasNext"),
        })

        if not items:
            break

        items_all.extend(items)

        total_pages = data.get("totalPages")
        has_next = data.get("hasNext")

        if (total_pages and page >= total_pages) or (has_next is False) or (len(items) < page_size):
            break

        page += 1

    return items_all, pages

def norm_code(x: pd.Series) -> pd.Series:
    return x.astype("string").str.strip()

def main():
    # ===== 1) VENDAS =====
    sales_params = {
        "BranchCnpj": "45877608000137",
        "StartDate": "2025-12-01T00:00:00Z",
        "EndDate": "2025-12-09T23:59:59Z",
    }

    sales_items, sales_pages = fetch_pages(
        "GET", URL_SALES,
        headers=headers,
        base_params=sales_params,
        page_size=1000,
        debug=True,                 # ✅ LIGA DEBUG
    )

    df_sales = pd.DataFrame([{
        "CNPJ Filial": i.get("branchCnpj"),
        "Sequência NF": i.get("invoiceSequence"),
        "Valor Venda": i.get("SaleValue"),
        "Data Venda": i.get("saleDate"),
        "Hora Venda": i.get("SaleHour"),
        "Status NF": i.get("invoiceStatus"),
        "Tipo Operação": i.get("operationType"),
        "operationCode": i.get("operationCode"),
    } for i in sales_items])

    if df_sales.empty:
        raise SystemExit("⚠️ Sem vendas para o período/filtro.")

    # ===== 2) OPERAÇÕES =====
    ops_payload = {
        "filter": {
            "branchCodeList": [5],
            "startMovementDate": "2025-12-01T00:00:00Z",
            "endMovementDate": "2025-12-09T00:00:00Z",
        }
    }

    ops_items, ops_pages = fetch_pages(
        "POST", URL_OPS,
        headers=headers,
        base_json=ops_payload,
        page_size=500,
        debug=True,                 # ✅ LIGA DEBUG
    )

    df_ops = pd.DataFrame([{
        "code": i.get("code"),
        "Nome Operação": i.get("name"),
        "Modelo": i.get("model"),
    } for i in ops_items]).drop_duplicates(subset=["code"], keep="first")

    if df_ops.empty:
        raise SystemExit("⚠️ Sem operações para o período/filtro.")

    # ===== 3) JOIN =====
    df_sales["operationCode"] = norm_code(df_sales["operationCode"])
    df_ops["code"] = norm_code(df_ops["code"])

    df_join = df_sales.merge(df_ops, left_on="operationCode", right_on="code", how="left")

    # ===== 4) EXPORT =====
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out = f"vendas_com_operacoes_{date_now}.xlsx"

    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        df_join.to_excel(w, "Vendas_JOIN", index=False)
        df_sales.to_excel(w, "Vendas_RAW", index=False)
        df_ops.to_excel(w, "Operacoes_RAW", index=False)
        pd.DataFrame(sales_pages).to_excel(w, "Paginacao_Vendas", index=False)
        pd.DataFrame(ops_pages).to_excel(w, "Paginacao_Operacoes", index=False)

    # Diagnóstico
    sem_match = df_join["Nome Operação"].isna().sum()
    print(f"✅ Gerado com Sucesso: {out}")
    print(f"🔎 Vendas sem match de operação: {sem_match}")

if __name__ == "__main__":
    main()
