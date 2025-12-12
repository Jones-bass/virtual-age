import requests
import pandas as pd
import json
import sys
import os
from datetime import datetime

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/person-fiscal-movement/search"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAGINAÇÃO ===
page = 1
page_size = 500
all_people = []
all_summaries = []

print("🚀 Iniciando consulta de Pessoas (Analytics + DEBUG)...")

while True:
    payload = {
        "filter": {
            "branchCodeList": [5],
            "startMovementDate": "2025-10-01T00:00:00Z",
            "endMovementDate": "2025-10-31T00:00:00Z",
        },
        "page": page,
        "pageSize": page_size,
    }

    print(f"\n📄 Consultando página {page} de pessoas…")
    resp = requests.post(URL, headers=headers, json=payload)
    print(f"📡 Status: {resp.status_code}")

    if resp.status_code != 200:
        print("❌ Erro na requisição:", resp.text)
        break

    try:
        data = resp.json()
    except requests.exceptions.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
        break

    # === DEBUG: SALVAR RESPOSTA ===
    debug_file = f"debug_response_people_page_{page}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resposta salva em: {debug_file}")

    # === DEBUG: ESTRUTURA ===
    print("🔍 Estrutura da resposta:")
    for key, value in data.items():
        tipo = type(value).__name__
        tam = len(value) if isinstance(value, (list, dict)) else "1"
        print(f"   - {key}: {tipo} ({tam})")

    print("🧩 Amostra (primeiros 1000 caracteres):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    print("-" * 60)

    # === PROCESSAMENTO DE DADOS ===
    items = data.get("items", [])
    if not items:
        print("⚠️ Nenhum registro encontrado nesta página.")
        break

    for item in items:
        addr = item.get("address", {}) or {}
        ind = item.get("individual", {}) or {}
        classifications = item.get("classifications", []) or []

        # Caso tenha múltiplas classificações, gera uma linha por classificação
        if classifications:
            for cls in classifications:
                all_people.append({
                    "Codigo": item.get("code"),
                    "CPF/CNPJ": item.get("cpfCnpj"),
                    "Nome": item.get("name"),
                    "TipoPessoa": item.get("personType"),
                    "Inativo": item.get("isInactive"),
                    "Nascimento": ind.get("birthDate"),
                    "EstadoCivil": ind.get("maritalStatus"),
                    "Genero": ind.get("gender"),
                    "Logradouro": addr.get("publicPlace"),
                    "Endereco": addr.get("address"),
                    "Numero": addr.get("addressNumber"),
                    "Bairro": addr.get("neighborhood"),
                    "Cidade": addr.get("cityName"),
                    "UF": addr.get("stateAbbreviation"),
                    "CEP": addr.get("cep"),
                    "Pais": addr.get("countryName"),
                    "ClassificacaoTipo": cls.get("typeName"),
                    "ClassificacaoCodigo": cls.get("code"),
                    "ClassificacaoNome": cls.get("name"),
                })
        else:
            # Pessoa sem classificação
            all_people.append({
                "Codigo": item.get("code"),
                "CPF/CNPJ": item.get("cpfCnpj"),
                "Nome": item.get("name"),
                "TipoPessoa": item.get("personType"),
                "Inativo": item.get("isInactive"),
                "Nascimento": ind.get("birthDate"),
                "EstadoCivil": ind.get("maritalStatus"),
                "Genero": ind.get("gender"),
                "Logradouro": addr.get("publicPlace"),
                "Endereco": addr.get("address"),
                "Numero": addr.get("addressNumber"),
                "Bairro": addr.get("neighborhood"),
                "Cidade": addr.get("cityName"),
                "UF": addr.get("stateAbbreviation"),
                "CEP": addr.get("cep"),
                "Pais": addr.get("countryName"),
                "ClassificacaoTipo": None,
                "ClassificacaoCodigo": None,
                "ClassificacaoNome": None,
            })

    summary = {
        "Page": page,
        "Count": data.get("count"),
        "TotalItems": data.get("totalItems"),
        "TotalPages": data.get("totalPages"),
    }
    all_summaries.append(summary)

    # === PAGINAÇÃO ===
    total_pages = data.get("totalPages")
    has_next = data.get("hasNext", False)

    if total_pages and page >= total_pages:
        print("✅ Todas as páginas foram processadas.")
        break
    elif not has_next or len(items) < page_size:
        print("✅ Última página (sem próxima).")
        break

    page += 1

# === EXPORTAÇÃO ===
df_people = pd.DataFrame(all_people)
df_summary = pd.DataFrame(all_summaries).drop_duplicates(subset=["Page"])

print("-" * 40)

if df_people.empty:
    print("⚠️ Nenhum dado encontrado para exportar.")
else:
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"pessoas_lista_{date_now}.xlsx"

    try:
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            df_people.to_excel(writer, sheet_name="Pessoas", index=False)
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name="ResumoPaginas", index=False)

        print(f"✅ Relatório gerado: {excel_file}")
        print(f"Total de registros exportados: {len(df_people)}")
    except Exception as e:
        print(f"❌ Erro ao exportar para Excel: {e}")
