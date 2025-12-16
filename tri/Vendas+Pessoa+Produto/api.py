import os
import sys
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

# === IMPORTA TOKEN ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from auth.config import TOKEN  # noqa: E402

# =========================
# CONFIG
# =========================
URL_MOV = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/fiscal-movement/search"
URL_PEO = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/person-fiscal-movement/search"
URL_PROD = "https://apitotvsmoda.bhan.com.br/api/totvsmoda/analytics/v2/product-fiscal-movement/search"

BRANCH_CODE_LIST = [5]
START = "2025-12-01T00:00:00Z"
END = "2025-12-16T23:59:59Z"
PAGE_SIZE = 500

# Produtos: filtro opcional (se não quiser, coloque None)
CLASSIFICATION_TYPE_CODE_LIST = [102]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# =========================
# ORDENAR LINHAS (REGISTROS)
# =========================
# A ordenação usa Data_dt (convertida de "Data"). Ajuste como quiser.
SORT_BY = ["Data_dt", "Operacao", "SKU"]
SORT_ASC = [True, True, True]

# =========================
# ORDEM DAS COLUNAS NO EXCEL
# =========================
COL_ORDER = [
    # --- MOVIMENTO ---
    "Codigo_Empresa",
    "Data",
    "Operacao",
    "Tipo",
    #"Estoque",
    "Representante",
    "Codigo_comprador",
    "Codigo_vendedor",

    # --- PRODUTO ---
    "SKU",
    "NomeProduto",
    "Codigo_Barra",
    "Referencia",
    #"NomeReferencia",
    "CodigoCor",
    "NomeCor",
    "Tamanho",


    # --- PESSOA ---
    "Codigo_pessoa",
    "CPF/CNPJ",
    "Nome",
    "TipoPessoa",
    #"Inativo",
    "Nascimento",
    "EstadoCivil",
    "Genero",
    "Cidade",
    "UF",
    "CEP",
    "Bairro",
    "Logradouro",
    "Endereco",
    "Numero",
    "Pais",
    #"ClassificacaoTipo",
    #"ClassificacaoCodigo",
    #"ClassificacaoNome",
    "QTD",
    "Valor_Bruto",
    "Desconto",
    "Valor_liquido",
]


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def paginate_post(
    session: requests.Session,
    url: str,
    filter_payload: Dict[str, Any],
    option_payload: Optional[Dict[str, Any]] = None,
    page_size: int = 100,
    timeout: int = 60,
) -> Iterable[Dict[str, Any]]:
    page = 1
    while True:
        payload: Dict[str, Any] = {
            "filter": filter_payload,
            "page": page,
            "pageSize": page_size,
        }
        if option_payload:
            payload["option"] = option_payload

        resp = session.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()

        data = resp.json() or {}
        items = data.get("items") or []
        if not items:
            break

        for it in items:
            yield it

        total_pages = data.get("totalPages")
        has_next = bool(data.get("hasNext", False))

        if total_pages is not None:
            if page >= int(total_pages):
                break
        else:
            if not has_next:
                break

        page += 1


# =========================
# MOVIMENTOS
# =========================
def fetch_movements(session: requests.Session) -> pd.DataFrame:
    filt = {
        "branchCodeList": BRANCH_CODE_LIST,
        "startMovementDate": START,
        "endMovementDate": END,
    }

    rows: List[Dict[str, Any]] = []
    for item in paginate_post(session, URL_MOV, filt, page_size=PAGE_SIZE):
        rows.append(
            {
                "Codigo_Empresa": item.get("branchCode"),
                "Codigo_pessoa": item.get("personCode"),
                "Representante": item.get("representativeCode"),
                "Data": item.get("movementDate"),
                "Operacao": item.get("operationCode"),
                "Tipo": item.get("operationModel"),
                "Codigo_comprador": item.get("buyerCode"),
                "Codigo_vendedor": item.get("sellerCode"),
                "Valor_Bruto": item.get("grossValue"),
                "Desconto": item.get("discountValue"),
                "Valor_liquido": item.get("netValue"),
                "SKU": item.get("productCode"),
                "Estoque": item.get("stockCode"),
                "QTD": item.get("quantity"),
            }
        )

    return pd.DataFrame(rows)


# =========================
# PESSOAS
# =========================
def fetch_people_exploded(session: requests.Session) -> pd.DataFrame:
    filt = {
        "branchCodeList": BRANCH_CODE_LIST,
        "startMovementDate": START,
        "endMovementDate": END,
    }

    rows: List[Dict[str, Any]] = []
    for item in paginate_post(session, URL_PEO, filt, page_size=PAGE_SIZE):
        addr = item.get("address") or {}
        ind = item.get("individual") or {}
        classifications = item.get("classifications") or []

        base = {
            "Codigo": item.get("code"),
            "CPF/CNPJ": item.get("cpfCnpj"),
            "Nome": item.get("name"),
            "TipoPessoa": item.get("personType"),
            "Inativo": item.get("isInactive"),
            "Nascimento": ind.get("birthDate"),
            "EstadoCivil": ind.get("maritalStatus"),
            "Genero": ind.get("gender"),
            "Logradouro": addr.get("publicPlace"),
            "Endereco": addr.get("address"),
            "Numero": addr.get("addressNumber"),
            "Bairro": addr.get("neighborhood"),
            "Cidade": addr.get("cityName"),
            "UF": addr.get("stateAbbreviation"),
            "CEP": addr.get("cep"),
            "Pais": addr.get("countryName"),
        }

        if classifications:
            for cls in classifications:
                rows.append(
                    {
                        **base,
                        "ClassificacaoTipo": cls.get("typeName"),
                        "ClassificacaoCodigo": cls.get("code"),
                        "ClassificacaoNome": cls.get("name"),
                    }
                )
        
        else:
            rows.append(
                {
                    **base,
                    "ClassificacaoTipo": None,
                    "ClassificacaoCodigo": None,
                    "ClassificacaoNome": None,
                }
            )

    return pd.DataFrame(rows)


def aggregate_people_for_join(df_people: pd.DataFrame) -> pd.DataFrame:
    if df_people.empty:
        return df_people

    df = df_people.copy()
    df["Codigo"] = df["Codigo"].astype("string").str.strip()

    def join_unique(series: pd.Series) -> Optional[str]:
        vals = [str(x).strip() for x in series.dropna().astype(str).tolist()]
        vals = [v for v in vals if v]
        return " | ".join(sorted(set(vals))) if vals else None

    return (
        df.groupby("Codigo", as_index=False)
        .agg(
            {
                "CPF/CNPJ": "first",
                "Nome": "first",
                "TipoPessoa": "first",
                "Inativo": "first",
                "Nascimento": "first",
                "EstadoCivil": "first",
                "Genero": "first",
                "Logradouro": "first",
                "Endereco": "first",
                "Numero": "first",
                "Bairro": "first",
                "Cidade": "first",
                "UF": "first",
                "CEP": "first",
                "Pais": "first",
  
            }
        )
    )


# =========================
# PRODUTOS
# =========================
def fetch_products_exploded(session: requests.Session) -> pd.DataFrame:
    filt = {
        "branchCodeList": BRANCH_CODE_LIST,
        "startMovementDate": START,
        "endMovementDate": END,
    }

    option = None
    if CLASSIFICATION_TYPE_CODE_LIST:
        option = {"classificationTypeCodeList": CLASSIFICATION_TYPE_CODE_LIST}

    rows: List[Dict[str, Any]] = []
    for item in paginate_post(session, URL_PROD, filt, option_payload=option, page_size=PAGE_SIZE):
        pc = item.get("productCode")
        if pc is None:
            continue
        try:
            if int(pc) == 0:
                continue
        except (TypeError, ValueError):
            continue

        classifications = item.get("classifications") or []
        base = {
            "CodigoProduto": item.get("productCode"),
            "NomeProduto": item.get("name"),
            "Referencia": item.get("referenceCode"),
            "Codigo_Barra": item.get("productSku"),
            "CodigoCor": item.get("colorCode"),
            "NomeCor": item.get("colorName"),
            "Tamanho": item.get("sizeName"),
        }


        if classifications:
            for cls in classifications:
                rows.append(
                    {
                        **base,
                        "Classificacao_Codigo": cls.get("code"),
                        "Colecao": cls.get("description"),
                    }
                )
        else:
            rows.append(
                {
                    **base,
                    "Classificacao_Codigo": None,
                    "Colecao": None,
                }
            )

    return pd.DataFrame(rows)


def aggregate_products_for_join(df_products: pd.DataFrame) -> pd.DataFrame:
    if df_products.empty:
        return df_products

    df = df_products.copy()
    df["CodigoProduto"] = df["CodigoProduto"].astype("string").str.strip()

    def join_unique(series: pd.Series) -> Optional[str]:
        vals = [str(x).strip() for x in series.dropna().astype(str).tolist()]
        vals = [v for v in vals if v]
        return " | ".join(sorted(set(vals))) if vals else None

    return (
        df.groupby("CodigoProduto", as_index=False)
        .agg(
            {
                "NomeProduto": "first",
                "Referencia": "first",
                "Codigo_Barra": "first",
                "CodigoCor": "first",
                "NomeCor": "first",
                "Tamanho": "first",
                "Classificacao_Codigo": join_unique,
                "Colecao": join_unique,
            }
        )
    )


# =========================
# EXPORT + UTIL
# =========================
def apply_column_order(df: pd.DataFrame, col_order: List[str]) -> pd.DataFrame:
    existing = [c for c in col_order if c in df.columns]
    rest = [c for c in df.columns if c not in existing]
    return df.reindex(columns=existing + rest)


def sort_rows(df: pd.DataFrame) -> pd.DataFrame:
    # cria coluna auxiliar Data_dt para ordenação correta
    if "Data" in df.columns:
        df = df.copy()
        df["Data_dt"] = pd.to_datetime(df["Data"], errors="coerce", utc=True)

    by = [c for c in SORT_BY if c in df.columns]
    if by:
        asc = SORT_ASC[: len(by)]
        df = df.sort_values(by=by, ascending=asc, na_position="last")

    # remove a coluna auxiliar se não quiser exportar
    if "Data_dt" in df.columns:
        df = df.drop(columns=["Data_dt"])

    return df


def export_excel(df: pd.DataFrame, prefix: str) -> str:
    date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{prefix}_{date_now}.xlsx"
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Dados", index=False)
    return filename


def main():
    session = make_session()

    # 1) Movimentos
    df_mov = fetch_movements(session)
    if df_mov.empty:
        print("⚠️ Nenhum movimento encontrado. Nada a exportar.")
        return

    # 2) Pessoas (agregado)
    df_peo = fetch_people_exploded(session)
    df_peo_agg = aggregate_people_for_join(df_peo)

    # Padroniza chaves
    df_mov["Codigo_pessoa"] = df_mov["Codigo_pessoa"].astype("string").str.strip()
    df_mov["SKU"] = df_mov["SKU"].astype("string").str.strip()

    # Join Movimentos + Pessoas
    df_join_01 = (
        df_mov.merge(
            df_peo_agg,
            how="left",
            left_on="Codigo_pessoa",
            right_on="Codigo",
            suffixes=("", "_Pessoa"),
        )
        .drop(columns=["Codigo"], errors="ignore")
    )

    missing_people = int(df_join_01["CPF/CNPJ"].isna().sum()) if "CPF/CNPJ" in df_join_01.columns else 0
    print(f"📌 Movimentos: {len(df_mov)}")
    print(f"📌 Pessoas (linhas): {len(df_peo)} | agregadas: {len(df_peo_agg)}")
    print(f"✅ Join (mov + pessoas): {len(df_join_01)} | sem match pessoa: {missing_people}")

    # 3) Produtos (agregado)
    df_prod = fetch_products_exploded(session)
    df_prod_agg = aggregate_products_for_join(df_prod)
    print(f"📌 Produtos (linhas): {len(df_prod)} | agregados: {len(df_prod_agg)}")

    # 4) JOIN FINAL: Movimentos (SKU) + Produtos (CodigoProduto)
    df_final = (
        df_join_01.merge(
            df_prod_agg,
            how="left",
            left_on="SKU",
            right_on="CodigoProduto",
            suffixes=("", "_Produto"),
        )
        .drop(columns=["CodigoProduto"], errors="ignore")
    )

    missing_prod = int(df_final["NomeProduto"].isna().sum()) if "NomeProduto" in df_final.columns else 0
    print(f"✅ Join final (inclui produto): {len(df_final)} | sem match produto: {missing_prod}")

    # 5) Ordenar linhas + ordenar colunas
    df_final = sort_rows(df_final)
    df_final = apply_column_order(df_final, COL_ORDER)

    # 6) Exportar
    out = export_excel(df_final, prefix="movimentos_pessoas_produtos")
    print(f"✅ Excel gerado: {out}")


if __name__ == "__main__":
    main()
