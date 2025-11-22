import requests
import json
from datetime import datetime
import sys
import os
import base64

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES ===
ACCESS_KEY = "32251041791600000445550010000027241197481362"  # 👉 substitua pela chave de acesso da NF-e
URL = f"https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/xml-contents/{ACCESS_KEY}"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print(f"🚀 Consultando XML da NF-e (chave: {ACCESS_KEY})...")

# === REQUISIÇÃO GET ===
try:
    response = requests.get(URL, headers=HEADERS, timeout=60)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"❌ Erro na conexão: {e}")
    sys.exit(1)
except json.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

print(f"📡 Status HTTP: {response.status_code}")

# === SALVA DEBUG ===
debug_file = f"debug_invoice_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Debug salvo em: {debug_file}")

# === CAMPOS ===
processing_type = data.get("processingType")
main_xml = data.get("mainInvoiceXml")
cancel_xml = data.get("cancelInvoiceXml")

print(f"📄 Status da NF-e: {processing_type}")

# === FUNÇÃO PARA SALVAR XML (com detecção de base64) ===
def save_xml(content, filename_prefix):
    if not content:
        return None

    try:
        # tenta decodificar base64
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        xml_content = decoded if decoded.strip().startswith("<") else content
    except Exception:
        xml_content = content  # caso não seja base64, salva como veio

    filename = f"{filename_prefix}_{ACCESS_KEY}_{datetime.now():%Y%m%d_%H%M%S}.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return filename

# === SALVA XML PRINCIPAL ===
main_file = save_xml(main_xml, "nfe_main")
if main_file:
    print(f"✅ XML principal salvo em: {main_file}")
else:
    print("⚠️ Nenhum XML principal retornado pela API.")

# === SALVA XML DE CANCELAMENTO ===
cancel_file = save_xml(cancel_xml, "nfe_cancel")
if cancel_file:
    print(f"⚠️ XML de cancelamento salvo em: {cancel_file}")

print("🏁 Consulta finalizada com sucesso.")
