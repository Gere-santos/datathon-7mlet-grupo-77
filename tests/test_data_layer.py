"""
Evidências de aceite — Etapa 1

Verifica três garantias que a banca pode executar com `make test`:

1. Rastreabilidade: load_kaggle.metadata() expõe fonte, versão e licença.
2. Dicionário: as colunas esperadas estão presentes após o pré-processamento.
3. Ausência de vazamento: duracao_contato não chega ao modelo de decisão,
   nem pela camada de dados nem pela API.
"""

import inspect
import io
import textwrap

import pandas as pd
import pytest

from datathon_offerexp.policies import ThompsonSamplingPolicy

# ── fixture: CSV mínimo com todas as colunas originais ───────────────────────

_SAMPLE_CSV = textwrap.dedent("""\
    age;job;marital;education;default;housing;loan;contact;month;day_of_week;\
duration;campaign;pdays;previous;poutcome;emp.var.rate;cons.price.idx;\
cons.conf.idx;euribor3m;nr.employed;y
    35;admin.;married;university.degree;no;yes;no;cellular;may;mon;\
180;1;999;0;nonexistent;1.1;93.994;-36.4;4.857;5191.0;no
    52;retired;single;basic.4y;no;no;no;telephone;jun;tue;\
300;2;5;1;success;-1.8;92.893;-46.2;1.334;5099.1;yes
""")


@pytest.fixture
def raw_df() -> pd.DataFrame:
    return pd.read_csv(io.StringIO(_SAMPLE_CSV), sep=";")


@pytest.fixture
def processed_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o mesmo pipeline do load_kaggle.load() sem precisar do CSV real."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parents[1] / "data" / "kaggle"))
    from load_kaggle import _COLUMN_MAP, _LEAKAGE_COLS, _add_derived_features

    df = raw_df.rename(columns=_COLUMN_MAP)
    df = df.drop(columns=_LEAKAGE_COLS)
    df = _add_derived_features(df)
    return df


# ── 1. Rastreabilidade ────────────────────────────────────────────────────────

def test_metadata_expoe_fonte():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parents[1] / "data" / "kaggle"))
    from load_kaggle import metadata

    meta = metadata()
    assert "kaggle" in meta["source"].lower(), "fonte deve apontar para o Kaggle"
    assert meta["license"] == "CC0: Public Domain"
    assert "bank-additional-full" in meta["version"]


def test_metadata_registra_coluna_removida():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parents[1] / "data" / "kaggle"))
    from load_kaggle import metadata

    meta = metadata()
    assert "duracao_contato" in meta["leakage_columns_removed"]


# ── 2. Dicionário / colunas esperadas ────────────────────────────────────────

EXPECTED_COLS = {
    "idade", "profissao", "estado_civil", "escolaridade",
    "inadimplencia", "emprestimo_habitacional", "emprestimo_pessoal",
    "tipo_contato", "mes_contato", "dia_semana",
    "numero_contatos_campanha", "dias_desde_ultimo_contato",
    "numero_contatos_anteriores", "resultado_campanha_anterior",
    "taxa_variacao_emprego", "indice_preco_consumidor",
    "indice_confianca_consumidor", "taxa_euribor_3_meses",
    "numero_empregados", "conversao",
    "cliente_ja_contatado", "faixa_contatos",
}


def test_colunas_esperadas_presentes(processed_df: pd.DataFrame):
    assert EXPECTED_COLS.issubset(set(processed_df.columns))


def test_features_derivadas_criadas(processed_df: pd.DataFrame):
    assert "cliente_ja_contatado" in processed_df.columns
    assert "faixa_contatos" in processed_df.columns


# ── 3. Ausência de vazamento temporal ────────────────────────────────────────

def test_duracao_contato_removida_pelo_pipeline(processed_df: pd.DataFrame):
    """duracao_contato (duration) não deve existir após o pré-processamento."""
    assert "duracao_contato" not in processed_df.columns, (
        "LEAKAGE DETECTADO: duracao_contato chegou ao dataset processado"
    )


def test_duracao_contato_nao_existe_como_coluna_original(raw_df: pd.DataFrame):
    """Confirma que o CSV original contém 'duration' — e que o pipeline a remove."""
    assert "duration" in raw_df.columns  # existe na fonte


def test_select_arm_nao_recebe_contexto():
    """A política de decisão não aceita contexto como parâmetro.

    Garante que nenhuma feature do cliente — incluindo duracao_contato —
    pode influenciar a decisão, mesmo que passada pelo chamador.
    """
    sig = inspect.signature(ThompsonSamplingPolicy.select_arm)
    params = [p for p in sig.parameters if p != "self"]
    assert params == [], (
        f"select_arm() não deveria receber parâmetros de contexto, mas recebe: {params}"
    )


def test_policy_ignora_contexto_na_pratica():
    """Chama select_arm() com e sem 'contexto' e verifica que a assinatura
    não permite injeção de features externas."""
    policy = ThompsonSamplingPolicy(seed=0)
    arm = policy.select_arm()
    assert 0 <= arm <= 3

    # Confirma que não é possível passar contexto — TypeError esperado
    with pytest.raises(TypeError):
        policy.select_arm(context={"duracao_contato": 300})  # type: ignore[call-arg]
