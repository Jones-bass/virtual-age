import requests
import pandas as pd
from datetime import datetime
import json
import sys
import os

# === IMPORTA TOKEN DE AUTH ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/person/v2/legal-entities/search"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

person_code_list = list(range(575, 580)) 

df_all_main = pd.DataFrame() 

all_raw_data = [] 

for person_code in person_code_list:
    payload = {
        "filter": {
            "change": {
                "startDate": "2024-11-16T23:06:55.925Z",
                "endDate": "2025-11-16T23:06:55.925Z",
                "inAddress": True, 
                "inPhone": True, 
                "inObservation": True,
                "inPerson": True 
            },
            "personCodeList": [person_code] 
        },
        "expand": "addresses,phones,emails", 
        "page": 1,
        "pageSize": 500
    }

    print(f"\n🚀 Iniciando consulta de PJ com código: {person_code}")

    # === REQUISIÇÃO POST E TRATAMENTO DE ERROS ===
    data = None
    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data and "items" in data and data["items"]:
                all_raw_data.extend(data["items"])

        else:
            print(f"❌ Erro HTTP {response.status_code} para {person_code}: {response.text[:100]}...")
            continue
            
    except requests.exceptions.JSONDecodeError:
        print(f"❌ Erro ao decodificar JSON da resposta para o código {person_code}.")
        continue
    except Exception as e:
        print(f"❌ Erro na requisição/conexão para {person_code}: {e}")
        continue
    
    if data is None:
        continue

    # === EXTRAÇÃO E NORMALIZAÇÃO DE DADOS EM LINHA ÚNICA ===
    items = data.get("items", [])
    
    if items:
        extracted_data = [] 
        
        for item in items:
            p_code = item.get("code")
            p_name = item.get("name")
            p_cnpj = item.get("cnpj")
            p_fantasy_name = item.get("fantasyName")
            
            addresses = item.get("addresses", [])
            phones = item.get("phones", [])
            emails = item.get("emails", [])
            
            # --- 1. Extração do Endereço Principal (APENAS O PRIMEIRO) ---
            address_fields = {
                "publicPlace": "N/D",
                "addressNumber": "S/N",
                "complement": "",
                "neighborhood": "N/D",
                "cityName": "N/D",
                "stateAbbreviation": "UF N/D",
                "cep": "N/D",
                "address_original": "N/D"
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
                address_fields["address_original"] = first_address.get('address', 'N/D')

            # Formata a string de Rua/Número/Complemento para uma coluna mais legível
            street_number_part = f"{address_fields['publicPlace']}"
            if address_fields['addressNumber'] and address_fields['addressNumber'] != 'S/N':
                street_number_part += f", {address_fields['addressNumber']}"
            if address_fields['complement']:
                street_number_part += f" ({address_fields['complement']})"

            # --- 2. Extração de Contatos Principais (O primeiro encontrado) ---
            phone_number = phones[0]['number'] if phones and phones[0].get('number') else "N/D"
            email_address = emails[0]['email'] if emails and emails[0].get('email') else "N/D"

            # Adiciona a linha de dados ao DataFrame
            extracted_data.append({
                "code": p_code,
                "cnpj": p_cnpj,
                "name": p_name,
                "Nome_Fantasia": p_fantasy_name,
                
                # Campos de Endereço Formatado (Primeiro Endereço)
                "Numero_Complemento": street_number_part,
                "Bairro": address_fields["neighborhood"],
                "Cidade_UF": f"{address_fields['cityName']}-{address_fields['stateAbbreviation']}",
                "CEP": address_fields["cep"],
                "Endereco": address_fields["address_original"], 
                
                # Contatos
                "Contato": phone_number,
                "Email": email_address,
            })

        # Cria o DataFrame para esta iteração e concatena
        df_main = pd.DataFrame(extracted_data)
        print(f"✅ {len(df_main)} registro encontrado e normalizado para o código {person_code}.")
        df_all_main = pd.concat([df_all_main, df_main], ignore_index=True)

    else:
        print(f"⚠️ Nenhum registro encontrado para o código {person_code}.")

# ---
## 💾 Consolidação Final de Debug
if all_raw_data:
    consolidated_debug_file = f"DEBUG_CONSOLIDADO_LEGAL_ENTITIES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(consolidated_debug_file, "w", encoding="utf-8") as f:
            # Salva a lista de todos os itens brutos consultados
            json.dump(all_raw_data, f, ensure_ascii=False, indent=2)
        print(f"\n✨ JSON de debug CONSOLIDADO salvo (Todos os {len(all_raw_data)} itens) em: {consolidated_debug_file}")
    except Exception as e:
        print(f"\n❌ Erro ao salvar JSON consolidado: {e}")

# ---
## 📝 EXPORTAÇÃO PARA EXCEL (Uma única aba)
excel_file = f"legal_entities_single_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    if not df_all_main.empty:
        final_columns = [
            "code", 
            "cnpj",
            "name", 
            "Nome_Fantasia",
            "Numero_Complemento", 
            "Bairro", 
            "Cidade_UF", 
            "CEP",
            "Endereco",
            "Contato",
            "Email" 
        ]
        
        cols_to_use = [col for col in final_columns if col in df_all_main.columns]
        df_all_main = df_all_main[cols_to_use]
        
        df_all_main.to_excel(excel_file, index=False, sheet_name="PJ_Dados_Consolidados")
        print(f"\n✅ Relatório Excel UNIFICADO gerado com sucesso: {excel_file}")
    else:
        print("\n⚠️ O DataFrame final está vazio. Nenhum arquivo Excel foi gerado.")
except Exception as e:
    print(f"\n❌ Erro ao exportar para Excel: {e}")

print("🏁 Execução finalizada com sucesso.")