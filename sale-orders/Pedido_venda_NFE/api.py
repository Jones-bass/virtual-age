import requests
import pandas as pd
import json
import time
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

URL = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/sales-order/v2/invoices"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def get_invoices(branch_code: int, order_codes: list[int], save_debug: bool = False, pause: float = 0.3) -> pd.DataFrame:
    all_items = []

    for order in order_codes:
        params = {"BranchCode": branch_code, "OrderCode": order}

        print(f"🔍 Buscando notas do pedido {order}...")

        try:
            resp = requests.get(URL, params=params, headers=HEADERS, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro de conexão para o pedido {order}: {e}")
            continue

        if resp.status_code != 200:
            print(f"❌ Erro ({resp.status_code}) ao buscar pedido {order}: {resp.text}")
            continue

        data = resp.json()

        if save_debug:
            debug_file = f"debug_invoices_order_{order}.json"
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON salvo: {debug_file}")

        invoices = data.get("invoices", [])
        if not invoices:
            print(f"⚠️ Nenhuma nota fiscal encontrada para o pedido {order}.")
            continue

        for nf in invoices:
            elec = nf.get("electronic", {})
            all_items.append({
                "Filial": nf.get("transactionBranchCode"),
                "Pedido": order,
                "NotaFiscal": nf.get("code"),
                "Série": nf.get("serial"),
                "DataEmissao": nf.get("issueDate"),
                "StatusNota": nf.get("status"),
                "Transportadora": nf.get("shippingCompanyName"),
                "Pacote": nf.get("packageNumber"),
                "PesoBruto": nf.get("grossWeight"),
                "PesoLiquido": nf.get("netWeight"),
                "QtdeItens": nf.get("quantity"),
                "ValorProduto": nf.get("productValue"),
                "ValorAdicional": nf.get("additionalValue"),
                "ValorFrete": nf.get("shippingValue"),
                "ValorSeguro": nf.get("InsuranceValue"),
                "ValorIPI": nf.get("ipiValue"),
                "ValorTotal": nf.get("totalValue"),
                "DataTransacao": nf.get("transactionDate"),
                "CodigoTransacao": nf.get("transactionCode"),
                # Campos eletrônicos
                "ChaveAcesso": elec.get("accessKey"),
                "SituacaoEletronica": elec.get("electronicInvoiceStatus"),
                "Recibo": elec.get("receipt"),
                "DataAutorizacao": elec.get("receivementDate")
            })

        # Aguarda entre as requisições para evitar bloqueios
        time.sleep(pause)

    if not all_items:
        print("⚠️ Nenhuma nota fiscal encontrada em nenhum pedido.")
        return pd.DataFrame()

    # === Cria DataFrame ===
    df = pd.DataFrame(all_items)

    # Conversão automática de colunas numéricas e de data
    for col in df.columns:
        if any(x in col.lower() for x in ["date", "emissao", "autorizacao", "transacao"]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif any(x in col.lower() for x in ["valor", "peso", "qtde"]):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print(f"✅ Total de notas coletadas: {len(df)}")
    return df


# EXECUÇÃO PRINCIPAL
if __name__ == "__main__":
    orders = [3188, 3217, 3225, 3240, 3251, 3252, 3255, 3258, 3259, 3260, 3261]
    filial = 3

    df = get_invoices(branch_code=filial, order_codes=orders, save_debug=False)

    if not df.empty:
        # Gera nome dinâmico com data e hora
        filename = f"relatorio_notas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Notas")

        print(f"📊 Relatório salvo com sucesso: {filename}")
    else:
        print("🚫 Nenhum dado foi retornado. Relatório não gerado.")
