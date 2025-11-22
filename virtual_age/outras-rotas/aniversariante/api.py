import requests
import pandas as pd
import json
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/seller-panel/seller/period-birthday"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_person_details = []

print("🚀 Iniciando consulta de Dados Cadastrais de Pessoas (Analytics + DEBUG)...")

while True:
    payload = {
        "datemin": "2025-12-01T00:00:00Z",
        "datemax": "2025-12-31T23:59:59Z",
        "page": page,
        "pageSize": page_size
    }

    print(f"\n👤 Consultando página {page} de registros de pessoas…")

    resp = requests.post(URL, headers=headers, json=payload)
    print(f"📡 Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === DEBUG: SALVAR RESPOSTA ===
    debug_file = f"debug_response_birthday_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: ESTRUTURA DO JSON ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    print("🧩 Amostra JSON (primeiros 1000 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    print("-" * 60)

    # === PROCESSAMENTO ===
    person_rows = data.get("dataRow", [])
    items_to_check = person_rows

    if not items_to_check:
        if page == 1:
            print("⚠️ Nenhuma pessoa encontrada para os filtros aplicados.")
        else:
            print("✅ Paginação concluída (não há mais dados).")
        break

    for item in person_rows:
        all_person_details.append({
            "CodigoPessoa": item.get("personCode"),
            "NomePessoa": item.get("personName"),
            "Documento": item.get("documentNumber"),
            "Telefone": item.get("phoneNumber"),
            "DataNascimento": item.get("birthdayDate"),
        })

    if len(person_rows) < page_size:
        print("✅ Paginação concluída (última página).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_details = pd.DataFrame(all_person_details)

print("-" * 30)

if df_details.empty:
    print("⚠️ Nenhum dado para exportar.")
else:
    excel_file = f"cadastro_pessoas.xlsx"
    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_details.to_excel(writer, sheet_name="DetalhesPessoas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros: {len(df_details)}")
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
