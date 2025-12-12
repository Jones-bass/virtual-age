import requests
import pandas as pd
from datetime import datetime
import json
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
# Certifique-se de que o TOKEN está configurado corretamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/individuals/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Lista de diferentes códigos de pessoa (exemplo)
person_code_list = list(range(200,300)) 

# DataFrame para acumular todos os dados
df_all_main = pd.DataFrame()

# Loop para realizar múltiplas consultas
for person_code in person_code_list:
    payload = {
        "filter": {
            "change": {
                "startDate": "2024-11-16T23:06:55.925Z",
                "endDate": "2025-11-16T23:06:55.925Z",
                "inPerson": True,
                "inAddress": True, 
                "inPhone": True,    
                "inObservation": True
            },
            "personCodeList": [person_code]
        },
        "expand": "addresses,phones,emails", 
        "page": 1,
        "pageSize": 1000
    }

    print(f"\n🚀 Iniciando consulta de indivíduo com código: {person_code}")

    # === REQUISIÇÃO POST ===
    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code} para {person_code}: {response.text[:100]}...")
            continue
        data = response.json()
    except Exception as e:
        print(f"❌ Erro na requisição/JSON para {person_code}: {e}")
        continue
    
    # === EXTRAÇÃO E NORMALIZAÇÃO DE DADOS ===
    items = data.get("items", [])
    
    if items:
        extracted_data = [] 
        
        for item in items:
            p_code = item.get("code")
            p_name = item.get("name")
            addresses = item.get("addresses", [])
            phones = item.get("phones", [])
            emails = item.get("emails", [])
            
            # --- 1. Extração de Endereço Principal (Campos separados + campo 'address') ---
            address_fields = {
                "publicPlace": "N/D",
                "addressNumber": "S/N",
                "complement": "",
                "neighborhood": "N/D",
                "cityName": "N/D",
                "stateAbbreviation": "UF N/D",
                "cep": "N/D",
                "address": "N/D" # O campo 'address' do JSON
            }
            
            if addresses:
                first_address = addresses[0]
                
                address_fields["publicPlace"] = first_address.get('publicPlace', 'Rua N/D')
                address_fields["addressNumber"] = str(first_address.get('addressNumber', 'S/N')) 
                address_fields["complement"] = first_address.get('complement', '')
                address_fields["neighborhood"] = first_address.get('neighborhood', 'Bairro N/D')
                address_fields["cityName"] = first_address.get('cityName', 'Cidade N/D')
                address_fields["stateAbbreviation"] = first_address.get('stateAbbreviation', 'UF N/D')
                address_fields["cep"] = first_address.get('cep', 'N/D')
                address_fields["address"] = first_address.get('address', 'N/D') # Adicionando o campo 'address'

            # Formata a string de Rua/Número/Complemento para uma coluna mais legível
            street_number_part = f"{address_fields['publicPlace']}"
            if address_fields['addressNumber'] and address_fields['addressNumber'] != 'S/N':
                street_number_part += f", {address_fields['addressNumber']}"
            if address_fields['complement']:
                street_number_part += f" ({address_fields['complement']})"

            # --- 2. Extração de Contatos Principais ---
            phone_number = "N/D"
            if phones and phones[0].get('number'):
                phone_raw = phones[0]['number']
                phone_number = phone_raw

            email_address = "N/D"
            if emails and emails[0].get('email'):
                email_address = emails[0]['email']
            
            extracted_data.append({
                "code": p_code,
                "name": p_name,
                # Novo Endereço Formatado
                "Rua_Numero_Complemento": street_number_part,
                "Bairro": address_fields["neighborhood"],
                "Cidade_UF": f"{address_fields['cityName']}-{address_fields['stateAbbreviation']}",
                "CEP": address_fields["cep"],
                # Campo 'address' original da API
                "address_original": address_fields["address"], 
                # Contatos
                "Telefone_Principal": phone_number,
                "Email_Principal": email_address,
            })

        # Cria o DataFrame para esta iteração e concatena
        df_main = pd.DataFrame(extracted_data)
        print(f"✅ {len(df_main)} registros encontrados e normalizados para o código {person_code}.")
        df_all_main = pd.concat([df_all_main, df_main], ignore_index=True)

    else:
        print(f"⚠️ Nenhum registro encontrado para o código {person_code}.")

# ---
# === EXPORTAÇÃO PARA EXCEL ===
excel_file = f"individuals_data_separated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    if not df_all_main.empty:
        # Garante que as colunas apareçam na ordem lógica no Excel
        final_columns = [
            "code", 
            "name", 
            "Rua_Numero_Complemento", 
            "Bairro", 
            "Cidade_UF", 
            "CEP",
            "address_original", # Adicionada nova coluna
            "Telefone_Principal", # Adicionada nova coluna
            "Email_Principal"    # Adicionada nova coluna
        ]
        df_all_main = df_all_main[final_columns]
        
        df_all_main.to_excel(excel_file, index=False, sheet_name="Individuals")
        print(f"\n✅ Relatório Excel gerado com sucesso: {excel_file}")
    else:
        print("\n⚠️ O DataFrame final está vazio. Nenhum arquivo Excel foi gerado.")
except Exception as e:
    print(f"\n❌ Erro ao exportar para Excel: {e}")

print("🏁 Execução finalizada com sucesso.")