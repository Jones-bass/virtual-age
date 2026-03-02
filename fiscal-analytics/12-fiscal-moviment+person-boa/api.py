import requests
import pandas as pd
import json
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API - MOVIMENTOS FISCAIS ===
URL_MOVEMENT = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/fiscal-movement/search"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === CONFIGURAÇÕES DA API - PESSOAS ===
URL_PEOPLE = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/person-fiscal-movement/search"

# === PAGINAÇÃO ===
page = 1
page_size = 1000
all_movements = []
all_people = []
all_summaries = []

print("🚀 Iniciando consulta de Movimentos Fiscais e Pessoas (Analytics FULL)…")

# === CONSULTA DE MOVIMENTOS FISCAIS ===
while True:
    payload = {
        "page": page,
        "pageSize": page_size,
        "filter": {
            "branchCodeList": [3],  
            "startMovementDate": "2026-02-01T00:00:00Z",
            "endMovementDate": "2026-02-28T23:59:59Z",
        }
    }

    print(f"\n📄 Consultando página {page} de Movimentos Fiscais…")
    resp = requests.post(URL_MOVEMENT, headers=headers, json=payload)
    print(f"📡 Status HTTP: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro:", resp.text)
        break

    try:
        data = resp.json()
    except:
        print("❌ Erro ao interpretar JSON da resposta.")
        break

    # === SALVAR RESPOSTA - MOVIMENTOS FISCAIS ===
    debug_file = f"debug_fiscal_movement_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Armazenado: {debug_file}")

    # === PROCESSAMENTO DE DADOS - MOVIMENTOS FISCAIS ===
    items = data.get("items", [])

    if not items:
        print("⚠️ Nenhum movimento real encontrado nesta página.")
        break

    for item in items:
        all_movements.append({
            "Filial": item.get("branchCode"),
            "Produto": item.get("productCode"),
            "Pessoa": item.get("personCode"),  # O código do cliente
            "DataMovimento": item.get("movementDate"),
            "Operacao": item.get("operationCode"),
            "ModeloOperacao": item.get("operationModel"),
            "ValorBruto": item.get("grossValue"),
            "ValorDesconto": item.get("discountValue"),
            "ValorLiquido": item.get("netValue"),
            "Quantidade": item.get("quantity"),
        })

    summary = {
        "Page": page,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
        "HasNext": data.get("hasNext")
    }
    all_summaries.append(summary)

    page += 1
    total_pages = data.get("totalPages", 0)
    has_next = data.get("hasNext", False)

    if not has_next or page >= total_pages:
        print("✅ Fim da paginação de Movimentos Fiscais.")
        break

# === CONSULTA DE PESSOAS ===
page = 1
while True:
    payload = {
        "filter": {
            "branchCodeList": [5],
            "startMovementDate": "2025-09-01T00:00:00Z",
            "endMovementDate": "2025-09-30T00:00:00Z",
        },
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n📄 Consultando página {page} de Pessoas…")
    resp = requests.post(URL_PEOPLE, headers=headers, json=payload)
    print(f"📡 Status HTTP: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro:", resp.text)
        break

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === SALVAR RESPOSTA - PESSOAS ===
    debug_file = f"debug_response_people_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === PROCESSAMENTO DE DADOS - PESSOAS ===
    items = data.get("items", [])
    if not items:
        print("⚠️ Nenhum registro de pessoa encontrado nesta página.")
        break

    for item in items:
        all_people.append({
            "Codigo": item.get("code"),
            "CPF/CNPJ": item.get("cpfCnpj"),
            "Nome": item.get("name"),
            "TipoPessoa": item.get("personType"),
            "Inativo": item.get("isInactive"),
            "Nascimento": item.get("birthDate"),
            "EstadoCivil": item.get("maritalStatus"),
            "Genero": item.get("gender"),
            "Endereco": item.get("address", {}).get("address", ""),
            "Cidade": item.get("address", {}).get("cityName", ""),
            "UF": item.get("address", {}).get("stateAbbreviation", ""),
            "CEP": item.get("address", {}).get("cep", ""),
            "Pais": item.get("address", {}).get("countryName", ""),
        })

    page += 1
    total_pages = data.get("totalPages", 0)
    has_next = data.get("hasNext", False)

    if not has_next or page >= total_pages:
        print("✅ Fim da paginação de Pessoas.")
        break

# === JUNÇÃO DOS DADOS ===
df_movements = pd.DataFrame(all_movements)
df_people = pd.DataFrame(all_people)

# Realizando o merge com base no código do cliente (personCode)
df_combined = pd.merge(df_movements, df_people, left_on="Pessoa", right_on="Codigo", how="left")

# === EXPORTAÇÃO DOS RESULTADOS ===
date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
excel_file = f"movimentos_fiscais_com_pessoas_{date_now}.xlsx"

with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_combined.to_excel(writer, sheet_name="MovimentosFiscaisComPessoas", index=False)
    print(f"✅ Relatório gerado: {excel_file}")
    print(f"Total de registros coletados: {len(df_combined)}")
