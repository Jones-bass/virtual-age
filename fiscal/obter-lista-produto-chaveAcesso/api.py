import os
import sys
import json
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import time 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from auth.config import TOKEN 

# === CONFIGURAÇÕES GERAIS ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/fiscal/v2/invoice-products/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}", 
    "Content-Type": "application/json"
}

# === FUNÇÕES UTILITÁRIAS ===
def log(msg: str):
    """Adiciona timestamp ao log."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def make_payload(page: int = 1, pageSize: int = 100) -> Dict[str, Any]:
    
    return {
        "filter": {
            "branchCodeList": [2],
            "acessKeyList": ["32251041791600000445550010000025031944883699"]
        },
        "expand": "batchItems", 
        "order": "invoiceSequence",
    }
    
def fetch_all_invoice_products() -> List[Dict[str, Any]]:
    """Busca todos os itens de NF de forma paginada."""
    all_items = []
    page = 1
    page_size = 100 

    log("🔎 Iniciando busca paginada por produtos de notas fiscais...")
    while True:
        payload = make_payload(page, page_size)
        try:
            log(f"   - Buscando página {page}...")
            response = requests.post(URL, headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                log(f"   - Página {page} não retornou itens. Fim da busca.")
                break 
            
            all_items.extend(items)
            log(f"   - {len(items)} itens retornados na página {page}. Total acumulado: {len(all_items)}")
            
            # Condição de parada baseada no total de itens retornado pela API
            if len(items) < page_size:
                log("   - Número de itens menor que o page_size. Fim da busca.")
                break
                
            page += 1
            time.sleep(0.3) # Adiciona um pequeno delay para evitar sobrecarga
        
        except requests.RequestException as e:
            log(f"❌ Erro ao consultar itens de NF na página {page}: {e}")
            log(f"Detalhes do erro: {response.text if 'response' in locals() else 'N/A'}")
            break 

    log(f"✅ Total final de itens de NF retornados: {len(all_items)}")
    return all_items

# === PROCESSAMENTO DE DADOS (NOVA LÓGICA) ===

def process_data(items: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    df_dicts = {"InvoiceProducts": [], "BatchItems": []}

    for item in items:
        df_dicts["InvoiceProducts"].append({
            "branchCode": item.get("branchCode"),
            "branchCnpj": item.get("branchCnpj"),
            "invoiceSequence": item.get("invoiceSequence"),
            "invoiceDate": item.get("invoiceDate"),
            "personCode": item.get("personCode"),
            "personName": item.get("personName"),
            "personCpfCnpj": item.get("personCpfCnpj"),
            "invoiceCode": item.get("invoiceCode"),
            "serialCode": item.get("serialCode"),
            "invoiceStatus": item.get("invoiceStatus"),
            "transactionBranchCode": item.get("transactionBranchCode"),
            "transactionDate": item.get("transactionDate"),
            "transactionCode": item.get("transactionCode"),
            "origin": item.get("origin"),
            "documentType": item.get("documentType"),
            "operationType": item.get("operationType"),
            "operationCode": item.get("operationCode"),
            "operatioName": item.get("operatioName"),
            "issueDate": item.get("issueDate"),
            "accessKey": item.get("accessKey"),
            "couponCode": item.get("couponCode"),
            "serialMachine": item.get("serialMachine"),
            "productCode": item.get("productCode"),
            "productName": item.get("productName"),
            "quantity": item.get("quantity"),
            "unitGrossValue": item.get("unitGrossValue"),
            "unitDiscountValue": item.get("unitDiscountValue"),
            "unitNetValue": item.get("unitNetValue"),
            "itemSequence": item.get("itemSequence"),
            "itemCode": item.get("itemCode"),
            "itemName": item.get("itemName"),
            "ncm": item.get("ncm"),
            "cfop": item.get("cfop"),
            "measureUnit": item.get("measureUnit"),
            "kitCode": item.get("kitCode"),
            "kitSequence": item.get("kitSequence"),
            "returnedQuantity": item.get("returnedQuantity"),
        })

        for b in item.get("batchItems", []):
            df_dicts["BatchItems"].append({
                "invoiceSequence": item.get("invoiceSequence"), # Chave de rastreio
                "invoiceCode": item.get("invoiceCode"), # Chave de rastreio
                "productCode": item.get("productCode"), # Chave de rastreio
                "itemSequence": item.get("itemSequence"), # Chave de rastreio
                "branchCode": b.get("branchCode"),
                "invoiceDate": b.get("invoiceDate"),
                "invoiceItemNumber": b.get("invoiceItemNumber"),
                "productCodeBatch": b.get("productCode"), # Renomeado para evitar conflito com productCode principal
                "sequence": b.get("sequence"),
                "branchCodeBatch": b.get("branchCodeBatch"),
                "batchNumber": b.get("batchNumber"),
                "itemBatchNumber": b.get("itemBatchNumber"),
                "quantityBatch": b.get("quantityBatch"),
                "batchBarcode": b.get("batchBarcode")
            })

    # Converte os dicionários em DataFrames
    dfs = {name: pd.DataFrame(data) for name, data in df_dicts.items()}
    return dfs

# === EXECUÇÃO ===
if __name__ == "__main__":
    log("🚀 Iniciando consulta de itens de NF...")
    all_items = fetch_all_invoice_products()

    # === SALVA DEBUG ===
    debug_file = f"debug_invoice_products_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    log(f"💾 Arquivo debug salvo: {debug_file}")

    if not all_items:
        sys.exit(0)

    # === PROCESSA E CONVERTE EM DATAFRAMES ===
    dfs = process_data(all_items)

    # === EXPORTA PARA EXCEL ===
    excel_file = f"invoice_products_full_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        for name, df in dfs.items():
            if not df.empty:
                df.to_excel(writer, index=False, sheet_name=name)

    log(f"✅ Excel completo gerado: {excel_file}")
    log(f"📊 Total de linhas em InvoiceProducts: {len(dfs['InvoiceProducts'])}")