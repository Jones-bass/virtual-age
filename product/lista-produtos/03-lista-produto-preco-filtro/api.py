import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import time 

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from auth.config import TOKEN

# === FUNÇÕES AUXILIARES (ADICIONADAS PARA CORRIGIR O ERRO) ===
def safe_list(value):
    """Garante que o valor é uma lista ou retorna uma lista vazia."""
    return value if isinstance(value, list) else []

def safe_dict(value):
    """Garante que o valor é um dicionário ou retorna um dicionário vazio."""
    return value if isinstance(value, dict) else {}

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/product/v2/prices/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🚀 Consultando preços de produtos...")

payload = {
    "filter": {
        "change": {
            "startDate": "2023-09-01T00:00:00Z",
            "endDate": "2025-09-30T23:59:59Z",
            "inBranchInfo": True,
            "branchInfoCodeList": [1],
        },
     
        "branchInfo": {
            "branchCode": 1, 
            "isActive": True,
            "isFinishedProduct": True
            },
    },
        
    "option": {
        "prices": [
            {
                "branchCode": 1,        
                "priceCodeList": [1, 2]
            }
        ],
    },
    "order": "productCode",
    "expand": "digitalPromotionPrices" 
}

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=60)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão: {e}")
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
debug_file = f"debug_product_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === PROCESSA RESPOSTA ===
items = data.get("items", [])
if not items:
    print("⚠️ Nenhum produto retornado pela API.")
    sys.exit(0)

# Inicializa novas listas para armazenar os dados complexos
produtos = []
precos = []
outras_promocoes = []
promocoes_digitais = []

for item in items:
    product_code = item.get("productCode")

    # === TABELA PRINCIPAL: PRODUTOS ===
    produtos.append({
        "productCode": product_code,
        "productName": item.get("productName"),
        "productSku": item.get("productSku"),
        "referenceCode": item.get("referenceCode"),
        "colorCode": item.get("colorCode"),
        "colorName": item.get("colorName"),
        "sizeName": item.get("sizeName"),
        "maxChangeFilterDate": item.get("maxChangeFilterDate")
    })

    # === PREÇOS E PROMOÇÕES REGULARES ===
    for preco in safe_list(item.get("prices")):
        promo_info = safe_dict(preco.get("promotionalInformation"))

        # Registro principal de Preços (aba 'Precos')
        precos.append({
            "productCode": product_code,
            "branchCode": preco.get("branchCode"),
            "priceCode": preco.get("priceCode"),
            "priceName": preco.get("priceName"),
            "price": preco.get("price"),
            "promotionalPrice": preco.get("promotionalPrice"),
            "promo_branchCode": promo_info.get("branchCode"),
            "promo_code": promo_info.get("code"),
            "promo_description": promo_info.get("description"),
            "promo_startDate": promo_info.get("startDate"),
            "promo_endDate": promo_info.get("endDate"),
        })

        # Lista de Outras Promoções (aba 'Outras_Promocoes')
        for outra_promo in safe_list(preco.get("informationOtherPromotions")):
            outras_promocoes.append({
                "productCode": product_code,
                "priceCode": preco.get("priceCode"), # Associa à tabela de Preços
                "branchCode": outra_promo.get("branchCode"),
                "promo_code": outra_promo.get("code"),
                "promo_description": outra_promo.get("description"),
                "promo_startDate": outra_promo.get("startDate"),
                "promo_endDate": outra_promo.get("endDate"),
                "price": outra_promo.get("price")
            })

    # === PROMOÇÕES DIGITAIS ===
    promo_digital = safe_dict(item.get("digitalPromotionPrices"))
    if promo_digital:
        # Registro principal de Promoção Digital (aba 'Promocoes_Digitais')
        promocoes_digitais.append({
            "productCode": product_code,
            "type": "Principal",
            "code": promo_digital.get("code"),
            "description": promo_digital.get("description"),
            "startDate": promo_digital.get("startDate"),
            "endDate": promo_digital.get("endDate"),
            "price": promo_digital.get("price"),
            "branchs": ", ".join(map(str, safe_list(promo_digital.get("branchs"))))
        })

        # Lista de Outras Promoções Digitais
        for outra_digital in safe_list(promo_digital.get("informationOtherDigitalPromotions")):
            promocoes_digitais.append({
                "productCode": product_code,
                "type": "Outra Digital",
                "code": outra_digital.get("code"),
                "description": outra_digital.get("description"),
                "startDate": outra_digital.get("startDate"),
                "endDate": outra_digital.get("endDate"),
                "price": outra_digital.get("price"),
                "branchs": ", ".join(map(str, safe_list(outra_digital.get("branchs"))))
            })


# === CONVERTE EM DATAFRAMES ===
df_produtos = pd.DataFrame(produtos)
df_precos = pd.DataFrame(precos)
df_outras_promocoes = pd.DataFrame(outras_promocoes)
df_promocoes_digitais = pd.DataFrame(promocoes_digitais)


# === EXPORTA PARA EXCEL ===
excel_file = f"product_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_produtos.to_excel(writer, index=False, sheet_name="Produtos")
    if not df_precos.empty:
        df_precos.to_excel(writer, index=False, sheet_name="Precos")
    if not df_outras_promocoes.empty:
        df_outras_promocoes.to_excel(writer, index=False, sheet_name="Outras_Promocoes")
    if not df_promocoes_digitais.empty:
        df_promocoes_digitais.to_excel(writer, index=False, sheet_name="Promocoes_Digitais")

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")