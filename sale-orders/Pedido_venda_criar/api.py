import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# URL da API
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sales-order/v2/b2c-orders"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def agora_iso():
    """
    Retorna data/hora atual no formato ISO UTC aceito pela API.
    Exemplo: 2026-07-08T13:58:38.021Z
    """
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# ==========================================================
# DADOS DO PEDIDO
# Ajuste os campos conforme seu cliente, produto, filial e regra fiscal
# ==========================================================
numero_personalizado = "602529"

order_id = f"MEU-PEDIDO-{numero_personalizado}"
customer_order_code = numero_personalizado
integration_code = numero_personalizado

data_atual = agora_iso()

payload = {
    "orderId": order_id,
    "branchCode": 2,
    "orderDate": data_atual,

    "customerOrderCode": customer_order_code,
    "integrationCode": integration_code,

    "customerCode": 110000009,

    "sellerCode": 9997,
    "priorityCode": 99,
    "representativeCode": 611,

    "statusOrder": "InProgress",

    "operationCode": 5101,
    "paymentConditionCode": 78,

    "totalAmountOrder":  5900.0,

    "items": {
        {
          "productCode": 9493,
          "quantity": 1,
          "price": 100.00
        },
    }
}


# ==========================================================
# ENVIO DA REQUISIÇÃO
# ==========================================================

try:
    print("🚀 Enviando pedido para a TOTVS Moda...")
    print(f"OrderId: {order_id}")
    print(f"CustomerOrderCode: {customer_order_code}")

    response = requests.post(
        URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    print(f"Status Code: {response.status_code}")

    # Tenta converter resposta em JSON
    try:
        response_json = response.json()
    except Exception:
        response_json = {
            "raw_response": response.text
        }

    # Salva payload enviado para debug
    with open("debug_create_order_payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Salva resposta da API para debug
    with open("debug_create_order_response.json", "w", encoding="utf-8") as f:
        json.dump(response_json, f, ensure_ascii=False, indent=2)

    print("💾 Payload salvo em: debug_create_order_payload.json")
    print("💾 Resposta salva em: debug_create_order_response.json")

    if response.status_code in [200, 201]:
        print("✅ Pedido criado com sucesso!")

        print("Resposta da API:")
        print(json.dumps(response_json, ensure_ascii=False, indent=2))

        print("\nResumo:")
        print(f"Filial: {response_json.get('branchCode')}")
        print(f"Código do Pedido TOTVS: {response_json.get('orderCode')}")
        print(f"OrderId: {response_json.get('orderId')}")

    else:
        print("❌ Erro ao criar pedido.")
        print("Resposta da API:")
        print(json.dumps(response_json, ensure_ascii=False, indent=2))

except requests.exceptions.Timeout:
    print("❌ Erro: tempo limite da requisição excedido.")

except requests.exceptions.ConnectionError:
    print("❌ Erro: falha de conexão com a API.")

except Exception as e:
    print(f"❌ Erro inesperado: {e}")