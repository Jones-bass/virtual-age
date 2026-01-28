import requests
import pandas as pd
import json
import sys
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# === CONFIGURAÇÕES DA API ===
URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sales-order/v2/billing-suggestions"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# === PARÂMETROS DE CONSULTA ===
PARAMS = {
    "BranchCode": 2,  # Empresa
    "SuggestionCode": 1282,  # Se quiser buscar uma sugestão específica
    "StartSuggestionDate": "2025-10-01T00:00:00Z",
    "EndSuggestionDate": "2025-11-03T23:59:59Z",
    "SuggestionStatusList": ["InProgress", "Closed"],  # Pode incluir "Canceled"
    "Order": "-branchCode,suggestionCode",
    "Expand": "items"
}

print("🚀 Iniciando consulta de Sugestões de Pedido (PEDFC001)...")
print(f"📦 Filtros: {json.dumps(PARAMS, indent=2)}")

# === REQUISIÇÃO ===
response = requests.get(URL, headers=headers, params=PARAMS)
print(f"📡 Status HTTP: {response.status_code}")

if response.status_code != 200:
    print("❌ Erro ao consultar sugestões:")
    print(response.text)
    sys.exit(1)

try:
    data = response.json()
except requests.exceptions.JSONDecodeError:
    print("❌ Erro ao decodificar JSON da resposta.")
    sys.exit(1)

# === SALVA JSON PARA DEBUG ===
debug_file = f"debug_suggestions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(debug_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"💾 Resposta completa salva em: {debug_file}")

# === INSPEÇÃO DE CHAVES ===
print("🔍 Estrutura principal da resposta:")
for key, value in data.items():
    tipo = type(value).__name__
    tamanho = len(value) if isinstance(value, (list, dict)) else "-"
    print(f"   - {key} ({tipo}) tamanho: {tamanho}")
print("-" * 60)

# === 1️⃣ DADOS PRINCIPAIS ===
main_fields = {
    "Count": data.get("count"),
    "TotalPages": data.get("totalPages"),
    "HasNext": data.get("hasNext"),
    "TotalItems": data.get("totalItems")
}
df_main = pd.DataFrame([main_fields])
print(f"✅ Dados principais extraídos: {len(df_main.columns)} campos.")

# === 2️⃣ LISTA DE SUGESTÕES ===
suggestion_list = []
order_list = []
item_list = []

if data.get("items"):
    for sug in data["items"]:
        suggestion_list.append({
            "BranchCode": sug.get("branchCode"),
            "SuggestionCode": sug.get("suggestionCode"),
            "StatusSuggestion": sug.get("statusSuggestion"),
            "SuggestionDate": sug.get("suggestionDate"),
            "MaxChangeFilterDate": sug.get("maxChangeFilterDate")
        })

        for order in sug.get("orders", []):
            order_data = {
                "BranchCode": sug.get("branchCode"),
                "SuggestionCode": sug.get("suggestionCode"),
                "OrderBranchCode": order.get("orderBranchCode"),
                "OrderCode": order.get("orderCode"),
                "Quantity": order.get("quantity"),
                "SuggestedQuantity": order.get("suggestedQuantity"),
                "PendingQuantity": order.get("pendingQuantity"),
                "Value": order.get("value"),
                "SuggestedValue": order.get("suggestedValue"),
                "PendingValue": order.get("pendingValue"),
            }
            order_list.append(order_data)

            for item in order.get("orderItems", []):
                item_data = {
                    "BranchCode": sug.get("branchCode"),
                    "SuggestionCode": sug.get("suggestionCode"),
                    "OrderCode": order.get("orderCode"),
                    "ProductCode": item.get("productCode"),
                    "Description": item.get("description"),
                    "StandardBarCode": item.get("standardBarCode"),
                    "SizeName": item.get("sizeName"),
                    "ColorName": item.get("colorName"),
                    "Quantity": item.get("quantity"),
                    "SuggestedQuantity": item.get("suggestedQuantity"),
                    "PendingQuantity": item.get("pendingQuantity"),
                    "Price": item.get("price")
                }
                item_list.append(item_data)

# === CONVERTE PARA DATAFRAMES ===
df_suggestions = pd.DataFrame(suggestion_list)
df_orders = pd.DataFrame(order_list)
df_items = pd.DataFrame(item_list)

print(f"📋 Total de sugestões encontradas: {len(df_suggestions)}")
print(f"📦 Total de pedidos vinculados: {len(df_orders)}")
print(f"🧾 Total de itens de pedido: {len(df_items)}")

# === 3️⃣ EXPORTAÇÃO PARA EXCEL ===
excel_file = f"sugestoes_{PARAMS['BranchCode']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

try:
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df_main.to_excel(writer, index=False, sheet_name="Resumo")
        if not df_suggestions.empty:
            df_suggestions.to_excel(writer, index=False, sheet_name="Sugestões")
        if not df_orders.empty:
            df_orders.to_excel(writer, index=False, sheet_name="Pedidos")
        if not df_items.empty:
            df_items.to_excel(writer, index=False, sheet_name="Itens")

    print(f"✅ Relatório Excel gerado com sucesso: {excel_file}")
except Exception as e:
    print(f"❌ Erro ao exportar para Excel: {e}")
