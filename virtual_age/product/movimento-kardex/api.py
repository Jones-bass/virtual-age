import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/kardex-movement"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Iniciando consulta paralela de movimentação de estoque (Kardex)...")

# === LISTA DE PRODUTOS ===
product_codes = list(range(1, 99))
branch_code = 2

# === INTERVALO DE DATAS ===
start_date = "2025-10-30T00:00:00Z"
end_date = "2025-10-31T23:59:59Z"

# === FUNÇÃO PARA CONSULTAR UM PRODUTO ===
def consultar_produto(code):
    params = {
        "BranchCode": branch_code,
        "ProductCode": code,
        "StartDate": start_date,
        "EndDate": end_date,
        "BalanceType": 1
    }

    try:
        response = requests.get(URL, headers=headers, params=params, timeout=60)
        if response.status_code == 204:
            return None, None
        if response.status_code != 200:
            return None, None

        data = response.json()

        produto = {
            "branchCode": data.get("branchCode"),
            "balanceType": data.get("balanceType"),
            "productCode": data.get("productCode"),
            "productDescription": data.get("productDescription"),
            "groupSequenceCode": data.get("groupSequenceCode"),
            "groupCode": data.get("groupCode"),
            "groupDescription": data.get("groupDescription"),
            "colorCode": data.get("colorCode"),
            "colorDescription": data.get("colorDescription"),
            "sizeDescription": data.get("sizeDescription"),
            "previousBalance": data.get("previousBalance")
        }

        movimentos = []
        for mv in data.get("movements", []):
            movimentos.append({
                "productCode": data.get("productCode"),
                "movementDate": mv.get("movementDate"),
                "historyCode": mv.get("historyCode"),
                "historyDescription": mv.get("historyDescription"),
                "operationCode": mv.get("operationCode"),
                "operationDescription": mv.get("operationDescription"),
                "documentType": mv.get("documentType"),
                "documentNumber": mv.get("documentNumber"),
                "unitValue": mv.get("unitValue"),
                "inQuantity": mv.get("inQuantity"),
                "outQuantity": mv.get("outQuantity"),
                "balance": mv.get("balance")
            })

        return produto, movimentos

    except Exception as e:
        print(f"❌ Erro no produto {code}: {e}")
        return None, None

# === EXECUÇÃO PARALELA ===
all_produtos = []
all_movimentos = []

start_time = time.time()
with ThreadPoolExecutor(max_workers=20) as executor:  # 20 threads em paralelo
    futures = {executor.submit(consultar_produto, code): code for code in product_codes}

    for future in as_completed(futures):
        code = futures[future]
        produto, movimentos = future.result()
        if produto:
            all_produtos.append(produto)
        if movimentos:
            all_movimentos.extend(movimentos)

print(f"\n⏱️ Tempo total: {round(time.time() - start_time, 2)} segundos")
print(f"📦 Produtos processados: {len(all_produtos)}")

# === EXPORTAÇÃO ===
df_produtos = pd.DataFrame(all_produtos)
df_movimentos = pd.DataFrame(all_movimentos)

excel_file = f"kardex_movement_parallel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    if not df_movimentos.empty:
        df_movimentos.to_excel(writer, index=False, sheet_name="Movimentos")

print(f"✅ Arquivo gerado: {excel_file}")
