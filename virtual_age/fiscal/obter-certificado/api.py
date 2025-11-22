import requests
import pandas as pd
import json
from datetime import datetime
import sys
import os
import base64

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/digital-certificates"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PARAMS = {
    "BranchCode": 1,               # Código da empresa
    "EnviromentType": "Official"   # Pode ser "Official" ou "Statement"
}

print("🚀 Consultando certificados digitais da empresa...")

# === REQUISIÇÃO GET ===
try:
    response = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=60)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na requisição: {e}")
    sys.exit(1)

# === SALVA DEBUG ===
debug_file = f"debug_digital_certificates_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === TRATAMENTO DOS DADOS ===
# Pode vir um único objeto ou lista, então padronizamos
items = data if isinstance(data, list) else [data]

certificados = []
for item in items:
    certificados.append({
        "sequence": item.get("sequence"),
        "description": item.get("description"),
        "password": item.get("password"),
        "expirationDate": item.get("expirationDate"),
        "idNumber": item.get("idNnumber"),
        "securityCode": item.get("securityCode"),
        "certificate": item.get("certifacate"),
        "content": item.get("content")
    })

# === EXPORTA PARA EXCEL ===
df = pd.DataFrame(certificados)
excel_file = f"digital_certificates_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
df.to_excel(excel_file, index=False)

print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
print(f"📦 Total de certificados exportados: {len(df)}")

# === OPCIONAL: salvar o conteúdo do certificado PFX ===
for i, item in enumerate(certificados, start=1):
    content = item.get("content")
    if content:
        try:
            pfx_data = base64.b64decode(content)
            pfx_file = f"certificate_{i}_{datetime.now():%Y%m%d_%H%M%S}.pfx"
            with open(pfx_file, "wb") as f:
                f.write(pfx_data)
            print(f"🔐 Certificado salvo em: {pfx_file}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar certificado {i}: {e}")
