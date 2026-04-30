import requests
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/individual-customers"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PAYLOAD DE CADASTRO ===
payload = {
    "branchInsertCode": 1,

    "cpf": "00000000000",

    "gender": "M",

}

print("🚀 Iniciando cadastro de cliente individual...")
print(f"📦 Payload enviado:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

# === REQUISIÇÃO POST ===
try:
    response = requests.post(URL, headers=headers, json=payload, timeout=60)
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão: {e}")
    sys.exit(1)

print(f"📡 Status HTTP: {response.status_code}")

# === TRATAMENTO DE ERRO HTTP ===
if response.status_code not in [200, 201]:
    print("❌ Erro na resposta da API:")
    print(response.text)

    error_file = f"erro_individual_customer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"💾 Erro salvo em: {error_file}")
    sys.exit(1)

# === TRATAMENTO DO JSON ===
try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    print(response.text)
    sys.exit(1)

# === SALVA DEBUG ===
debug_file = f"debug_individual_customer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"💾 Debug salvo em: {debug_file}")

# === RETORNO ESPERADO ===
customer_code = data.get("customerCode")

if customer_code is not None:
    print(f"✅ Cliente cadastrado com sucesso!")
    print(f"🆔 Código do cliente: {customer_code}")
else:
    print("⚠️ Cadastro realizado, mas customerCode não foi encontrado na resposta.")
    print(data)

print("🏁 Execução finalizada.")