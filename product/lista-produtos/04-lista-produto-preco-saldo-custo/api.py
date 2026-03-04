import requests
import pandas as pd
import json
from datetime import datetime
import sys
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === FUNÇÃO AUXILIAR ===
def safe_list(value):
    """Garante que o retorno seja sempre uma lista."""
    return value if isinstance(value, list) else []

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/costs/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando custos de produtos...")

# === FUNÇÃO PARA PEGAR DADOS COM PAGINAÇÃO ===
def get_all_data():
    all_items = []
    page = 1
    while True:
        # === REQUEST BODY ===
        payload = {
            "filter": {
             
                "branchInfo": {
                    "branchCode": 2,  # Empresa
                    "isActive": True,
                    "isFinishedProduct": True
                }
            },
            "option": {
                "costs": [
                    {
                        "branchCode": 2,        
                        "costCodeList": [2]
                    }
                ],
            },
            "page": page,
            "pageSize": 1000,  # Tamanho da página
            "order": "productCode",
            "expand": "digitalPromotionPrices"
        }

        # === REQUISIÇÃO POST ===
        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=60)
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
            page_data = response.json()
        except requests.exceptions.JSONDecodeError:
            print("❌ Erro ao decodificar JSON da resposta.")
            sys.exit(1)

        # Adiciona os itens da página atual
        items = page_data.get("items", [])
        all_items.extend(items)

        # Verifica se há mais páginas
        total_pages = page_data.get("totalPages", 0)
        if page >= total_pages:
            break

        page += 1  # Avança para a próxima página

    return all_items

# === CONSULTA DE DADOS ===
items = get_all_data()

if not items:
    print("⚠️ Nenhum produto retornado pela API.")
    sys.exit(0)

# Inicializa novas listas para armazenar os dados complexos
produtos = []
custos = []

for item in items:
    produtos.append({
        "productCode": item.get("productCode"),
        "productName": item.get("productName"),
        "productSku": item.get("productSku"),
        "referenceCode": item.get("referenceCode"),
        "colorCode": item.get("colorCode"),
        "colorName": item.get("colorName"),
        "sizeName": item.get("sizeName"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

    for c in safe_list(item.get("costs")):
        custos.append({
            "productCode": item.get("productCode"),
            "branchCode": c.get("branchCode"),
            "costCode": c.get("costCode"),
            "costName": c.get("costName"),
            "cost": c.get("cost")
        })

# === CONVERTE PARA DATAFRAMES ===
df_produtos = pd.DataFrame(produtos)
df_custos = pd.DataFrame(custos)

# === EXPORTA PARA EXCEL ===
excel_file = f"product_costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    if not df_custos.empty:
        df_custos.to_excel(writer, index=False, sheet_name="Custos")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")