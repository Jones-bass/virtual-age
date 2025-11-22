import requests
import pandas as pd
from datetime import datetime
import json
import time
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/general/v2/payment-conditions"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === VARIÁVEIS DE PAGINAÇÃO ===
PAGE_SIZE = 100
page = 1
all_records = []

print("🚀 Iniciando coleta de Condições de Pagamento TOTVS...")
print(f"📦 Endpoint: {URL}")
print(f"📄 Página inicial: {page} | Tamanho por página: {PAGE_SIZE}")
print("-" * 70)

while True:
    params = {
        "Page": page,
        "PageSize": PAGE_SIZE
    }

    print(f"\n📄 Buscando página {page}...")

    try:
        resp = requests.get(URL, headers=headers, params=params, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão na página {page}: {e}")
        break

    print(f"📡 Status HTTP: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:")
        print(resp.text)
        break

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === Salva resposta bruta para debug ===
    debug_file = f"debug_payment_conditions_page_{page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Debug salvo: {debug_file}")

    # === Extrai registros ===
    records = data.get("items", [])
    if not records:
        print("⚠️ Nenhum dado encontrado nesta página. Encerrando.")
        break

    all_records.extend(records)
    print(f"✅ Página {page}: {len(records)} registros | Total acumulado: {len(all_records)}")

    # === Verifica se há mais páginas ===
    if not data.get("hasNext", False):
        print("🏁 Última página alcançada.")
        break

    page += 1
    time.sleep(0.3)  # pausa para não sobrecarregar a API

print("-" * 70)

# === CRIAÇÃO DO DATAFRAME E EXPORTAÇÃO ===
if not all_records:
    print("⚠️ Nenhum registro retornado da API.")
else:
    df = pd.DataFrame(all_records)
    excel_file = f"condicoes_pagamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    try:
        df.to_excel(excel_file, index=False)
        print(f"✅ Total coletado: {len(df)} registros")
        print(f"📂 Arquivo salvo: {excel_file}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")

print("✅ Execução finalizada.")
