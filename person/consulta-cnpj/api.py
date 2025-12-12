import requests
import pandas as pd
import json   
from datetime import datetime
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
branch_id = "45877608000137"  # Pode ser o código interno ou CNPJ da empresa
URL = f"https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/branches/{branch_id}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print(f"🚀 Consultando dados da empresa branchId={branch_id}...")

# === REQUISIÇÃO GET ===
try:
    response = requests.get(URL, headers=headers, timeout=30)
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
debug_file = f"debug_branch_{branch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === EXTRAÇÃO DE DADOS ===
df_main = pd.DataFrame([{
    "branchCode": data.get("branchCode"),
    "personCode": data.get("personCode"),
    "cnpj": data.get("cnpj"),
    "personName": data.get("personName"),
    "fantasyName": data.get("fantasyName")
}])

# === ENDEREÇOS ===
addresses = data.get("addresses", [])
df_addresses = pd.DataFrame(addresses)

# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"branch_{branch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
    df_main.to_excel(writer, index=False, sheet_name="Branch")
    if not df_addresses.empty:
        df_addresses.to_excel(writer, index=False, sheet_name="Addresses")

print(f"✅ Relatório Excel gerado: {excel_file}")
