"""
Evidências de aceite — Etapa 2

Verifica que os arquivos sintéticos existem, têm o schema documentado
e estão separados da base Kaggle original.
Executável com `make test` sem dependências externas além dos CSVs versionados.
"""

from pathlib import Path

import pandas as pd
import pytest

_ROOT = Path(__file__).parents[1]
_SYNTH = _ROOT / "data" / "synthetic_enrichment"
_KAGGLE = _ROOT / "data" / "kaggle"

# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def catalog() -> pd.DataFrame:
    return pd.read_csv(_SYNTH / "offer_catalog.csv")


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    return pd.read_csv(_SYNTH / "offer_events.csv", nrows=100)


@pytest.fixture(scope="module")
def delayed() -> pd.DataFrame:
    return pd.read_csv(_SYNTH / "delayed_rewards.csv", nrows=100)


# ── separação física da base Kaggle ─────────────────────────────────────────

def test_arquivos_sinteticos_em_diretorio_proprio():
    assert _SYNTH.is_dir()
    assert _KAGGLE.is_dir()
    assert _SYNTH != _KAGGLE, "arquivos sintéticos devem estar fora de data/kaggle/"


def test_base_kaggle_nao_contaminada():
    data_extensions = {".csv", ".jsonl", ".parquet"}
    kaggle_data = {f.name for f in _KAGGLE.iterdir() if f.suffix in data_extensions}
    synth_data  = {f.name for f in _SYNTH.iterdir() if f.suffix in data_extensions}
    assert kaggle_data.isdisjoint(synth_data), (
        "nenhum arquivo de dados sintético deve ter o mesmo nome de um arquivo Kaggle"
    )


# ── schema: offer_catalog.csv ────────────────────────────────────────────────

def test_catalog_schema(catalog: pd.DataFrame):
    expected = {"arm_id", "arm_name", "arm_type", "description", "is_control"}
    assert expected.issubset(set(catalog.columns))


def test_catalog_tem_quatro_bracos(catalog: pd.DataFrame):
    assert len(catalog) == 4


def test_catalog_tem_um_controle(catalog: pd.DataFrame):
    assert catalog["is_control"].sum() == 1
    assert catalog.loc[catalog["is_control"], "arm_name"].iloc[0] == "sem_oferta"


def test_catalog_arm_ids_sequenciais(catalog: pd.DataFrame):
    assert list(catalog["arm_id"]) == [0, 1, 2, 3]


# ── schema: offer_events.csv ─────────────────────────────────────────────────

_EVENTO_COLS = {
    "event_id", "subject_key", "occurred_at", "channel",
    "arm_id", "arm_name", "reward",
}
_CONTEXTO_COLS = {
    "idade", "profissao", "estado_civil", "escolaridade",
    "cliente_ja_contatado", "faixa_contatos",
}


def test_events_colunas_de_evento(events: pd.DataFrame):
    assert _EVENTO_COLS.issubset(set(events.columns))


def test_events_contexto_incluido(events: pd.DataFrame):
    assert _CONTEXTO_COLS.issubset(set(events.columns)), (
        "contexto do cliente deve estar embutido em offer_events"
    )


def test_events_reward_binario(events: pd.DataFrame):
    assert set(events["reward"].unique()).issubset({0, 1})


def test_events_arm_id_valido(events: pd.DataFrame):
    assert set(events["arm_id"].unique()).issubset({0, 1, 2, 3})


def test_events_event_id_unico(events: pd.DataFrame):
    assert events["event_id"].is_unique


def test_events_sem_leakage_duracao(events: pd.DataFrame):
    assert "duracao_contato" not in events.columns
    assert "duration" not in events.columns


# ── schema: delayed_rewards.csv ──────────────────────────────────────────────

_DELAYED_COLS = {
    "event_id", "subject_key", "occurred_at", "channel",
    "arm_id", "arm_name", "reward",
    "delay_days", "reward_observed_at", "reward_type", "reward_status",
}


def test_delayed_schema(delayed: pd.DataFrame):
    assert _DELAYED_COLS.issubset(set(delayed.columns))


def test_delayed_horizonte_maximo_14_dias(delayed: pd.DataFrame):
    assert delayed["delay_days"].max() <= 14, (
        "horizonte temporal máximo documentado é 14 dias"
    )


def test_delayed_atraso_minimo_um_dia(delayed: pd.DataFrame):
    assert delayed["delay_days"].min() >= 1


def test_delayed_reward_type_valores(delayed: pd.DataFrame):
    esperados = {"conversao_confirmada", "sem_conversao_observada"}
    assert set(delayed["reward_type"].unique()).issubset(esperados)


def test_delayed_reward_status_valores(delayed: pd.DataFrame):
    esperados = {"confirmed", "not_converted"}
    assert set(delayed["reward_status"].unique()).issubset(esperados)


def test_delayed_event_ids_rastreavel_para_eventos(delayed: pd.DataFrame):
    events = pd.read_csv(_SYNTH / "offer_events.csv", usecols=["event_id"], nrows=100)
    assert delayed["event_id"].isin(events["event_id"]).all(), (
        "todo event_id em delayed_rewards deve existir em offer_events"
    )
