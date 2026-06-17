"""Carregamento e pré-processamento da base Kaggle Bank Marketing."""

from pathlib import Path

import pandas as pd

# ── Metadados da fonte ────────────────────────────────────────────────────────
SOURCE = "https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing"
VERSION = "bank-additional-full.csv (download junho/2025)"
LICENSE = "CC0: Public Domain"
CITATION = (
    "Moro, S., Cortez, P., & Rita, P. (2014). "
    "A data-driven approach to predict the success of bank telemarketing. "
    "Decision Support Systems, 62, 22–31."
)

_DEFAULT_PATH = Path(__file__).parent / "bank-additional-full.csv"

_COLUMN_MAP = {
    "age": "idade",
    "job": "profissao",
    "marital": "estado_civil",
    "education": "escolaridade",
    "default": "inadimplencia",
    "housing": "emprestimo_habitacional",
    "loan": "emprestimo_pessoal",
    "contact": "tipo_contato",
    "month": "mes_contato",
    "day_of_week": "dia_semana",
    "duration": "duracao_contato",       # descartada — ver nota abaixo
    "campaign": "numero_contatos_campanha",
    "pdays": "dias_desde_ultimo_contato",
    "previous": "numero_contatos_anteriores",
    "poutcome": "resultado_campanha_anterior",
    "emp.var.rate": "taxa_variacao_emprego",
    "cons.price.idx": "indice_preco_consumidor",
    "cons.conf.idx": "indice_confianca_consumidor",
    "euribor3m": "taxa_euribor_3_meses",
    "nr.employed": "numero_empregados",
    "y": "conversao",
}

# duracao_contato é conhecida apenas APÓS o contato → data leakage se usada
_LEAKAGE_COLS = ["duracao_contato"]


def load(csv_path: Path | str | None = None) -> pd.DataFrame:
    """Carrega, traduz e pré-processa a base Kaggle.

    Retorna DataFrame com colunas em português, sem vazamento temporal,
    e com as features derivadas `cliente_ja_contatado` e `faixa_contatos`.
    """
    path = Path(csv_path) if csv_path else _DEFAULT_PATH
    df = pd.read_csv(path, sep=";")
    df = df.rename(columns=_COLUMN_MAP)
    df = df.drop(columns=_LEAKAGE_COLS)
    df = _add_derived_features(df)
    return df


def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["cliente_ja_contatado"] = (df["dias_desde_ultimo_contato"] != 999).astype(int)
    df["faixa_contatos"] = pd.cut(
        df["numero_contatos_campanha"],
        bins=[0, 1, 3, 5, 10, 20, 100],
        labels=["1", "2-3", "4-5", "6-10", "11-20", "20+"],
    )
    return df


def metadata() -> dict:
    """Retorna dicionário com proveniência da base."""
    return {
        "source": SOURCE,
        "version": VERSION,
        "license": LICENSE,
        "citation": CITATION,
        "leakage_columns_removed": _LEAKAGE_COLS,
    }


def save_processed(df: pd.DataFrame, output_path: Path | str | None = None) -> Path:
    """Salva a tabela processada em data/processed/modeling_table.csv."""
    out = Path(output_path) if output_path else Path(__file__).parents[2] / "data" / "processed" / "modeling_table.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out


if __name__ == "__main__":
    df = load()
    meta = metadata()
    print(f"Fonte   : {meta['source']}")
    print(f"Versão  : {meta['version']}")
    print(f"Licença : {meta['license']}")
    print(f"Shape   : {df.shape}")
    print(f"Colunas : {list(df.columns)}")
    out = save_processed(df)
    print(f"Salvo   : {out}")
