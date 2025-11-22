import requests
import json
import sys
import os
import time

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# Definindo URL da API para criação de devolução
create_url = "https://treino.bhan.com.br:9443/api/totvsmoda/general/v2/devolutions/create"
# Definindo URL da API para consulta de devoluções
search_url = "https://treino.bhan.com.br:9443/api/totvsmoda/general/v2/devolutions/search"

# Definindo cabeçalhos
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Montando o payload com base no seu formato request para criação da devolução
payload = {
    "branchCode": 3,
    "operationCode": 173,
    "personCode": 740,
    "descriptionDevolution": "Devolucao do cliente Jones",
    "returnDate": "2025-11-06T00:22:27.028Z",
    "issueInvoiceDate": "2025-11-06T22:27:02.917Z",
    "invoiceNumber": 3582,
    "accessKey": "32251141791600000526550010000035821141721329",
    "fiscalDocumentType": 55,
    "authorizationNumber": "332250000283385",
    
    "classifications": [
    {
      "classificationTypeCode": 1,
      "classificationCode": "5"
    }
  ],
    "items": [
        {
            "productCode": 5102,
            "productSku": "7900000013396",
            "devolutionQuantity": 1,
            "netValue": 1855,
            "grossValue": 1855,
        }
    ]
}

# Enviando a requisição POST para a API para criar a devolução
response = requests.post(create_url, json=payload, headers=headers)

# Verificando a resposta da criação
if response.status_code == 201:  # Código 201 indica sucesso na criação do recurso
    print("Devolução processada com sucesso!")
    
    try:
        # Tentando decodificar a resposta JSON
        response_data = response.json()
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        # Extraindo o código de devolução (devolutionCode) da resposta
        devolution_code = response_data.get('devolutionCode', None)
        
        if devolution_code:
            print(f"📦 Código de devolução criado: {devolution_code}")
            
            # Agora, consulte a devolução usando o devolutionCode
            search_payload = {
                "branchCode": 3,  # Código da filial
                "devolutionCode": devolution_code  # Código da devolução criado
            }
            
            # Realizando a requisição GET para consultar a devolução criada
            status_response = requests.get(search_url, headers=headers, params=search_payload)
            
            if status_response.status_code == 200:
                print("✅ Status da devolução obtido com sucesso!")
                status_data = status_response.json()
                print(json.dumps(status_data, indent=2, ensure_ascii=False))
            else:
                print(f"❌ Erro ao consultar o status da devolução: {status_response.status_code}")
                print(status_response.text)
        else:
            print("⚠️ Não foi possível obter o código da devolução.")
    except json.JSONDecodeError:
        print("❌ Erro ao decodificar JSON da resposta.")
else:
    print(f"❌ Erro ao processar devolução. Status Code: {response.status_code}")
    try:
        # Tentando extrair detalhes do erro se a resposta for JSON
        response_data = response.json()
        print("🔴 Detalhes do erro:", json.dumps(response_data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("❌ A resposta não está no formato JSON.")
        print(response.text)

