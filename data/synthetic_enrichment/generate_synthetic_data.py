from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/processed/modeling_table.csv")
OUTPUT_DIR = Path("data/synthetic_enrichment")

RANDOM_SEED = 42

ARMS = {
    0: "sem_oferta",
    1: "educacao_financeira",
    2: "simulador_credito",
    3: "cartao_premium",
}

CHANNELS = ["app", "email", "web", "whatsapp"]


def generate_offer_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "arm_id": 0,
                "arm_name": "sem_oferta",
                "arm_type": "controle",
                "description": "Grupo controle sem oferta ativa.",
                "is_control": True,
            },
            {
                "arm_id": 1,
                "arm_name": "educacao_financeira",
                "arm_type": "conteudo",
                "description": "Conteúdo educativo sobre organização financeira.",
                "is_control": False,
            },
            {
                "arm_id": 2,
                "arm_name": "simulador_credito",
                "arm_type": "ferramenta",
                "description": "Simulador de crédito para avaliar opções disponíveis.",
                "is_control": False,
            },
            {
                "arm_id": 3,
                "arm_name": "cartao_premium",
                "arm_type": "produto",
                "description": "Oferta sintética de cartão premium.",
                "is_control": False,
            },
        ]
    )


def generate_offer_events(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    events = df.copy()

    events["event_id"] = [f"evt_{i:06d}" for i in range(1, len(events) + 1)]
    events["subject_key"] = [f"subject_{i:06d}" for i in range(1, len(events) + 1)]

    events["arm_id"] = rng.choice(list(ARMS.keys()), size=len(events))
    events["arm_name"] = events["arm_id"].map(ARMS)

    events["channel"] = rng.choice(CHANNELS, size=len(events))

    events["reward"] = (
        events["conversao"]
        .map({"yes": 1, "no": 0})
        .astype(int)
    )

    events["occurred_at"] = pd.date_range(
        start="2025-01-01",
        periods=len(events),
        freq="min",
    )

    cols_evento = [
        "event_id",
        "subject_key",
        "occurred_at",
        "channel",
        "arm_id",
        "arm_name",
        "reward",
    ]

    cols_contexto = [col for col in events.columns if col not in cols_evento]

    return events[cols_evento + cols_contexto]


def generate_delayed_rewards(offer_events: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)

    delayed_rewards = offer_events[
        [
            "event_id",
            "subject_key",
            "occurred_at",
            "channel",
            "arm_id",
            "arm_name",
            "reward",
        ]
    ].copy()

    delayed_rewards["delay_days"] = np.where(
        delayed_rewards["reward"] == 1,
        rng.integers(1, 15, size=len(delayed_rewards)),
        rng.integers(1, 8, size=len(delayed_rewards)),
    )

    delayed_rewards["reward_observed_at"] = (
        pd.to_datetime(delayed_rewards["occurred_at"])
        + pd.to_timedelta(delayed_rewards["delay_days"], unit="D")
    )

    delayed_rewards["reward_type"] = np.where(
        delayed_rewards["reward"] == 1,
        "conversao_confirmada",
        "sem_conversao_observada",
    )

    delayed_rewards["reward_status"] = np.where(
        delayed_rewards["reward"] == 1,
        "confirmed",
        "not_converted",
    )

    return delayed_rewards


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)

    offer_catalog = generate_offer_catalog()
    offer_events = generate_offer_events(df)
    delayed_rewards = generate_delayed_rewards(offer_events)

    offer_catalog.to_csv(OUTPUT_DIR / "offer_catalog.csv", index=False)
    offer_events.to_csv(OUTPUT_DIR / "offer_events.csv", index=False)
    delayed_rewards.to_csv(OUTPUT_DIR / "delayed_rewards.csv", index=False)

    print("Arquivos gerados com sucesso:")
    print(f"- {OUTPUT_DIR / 'offer_catalog.csv'}")
    print(f"- {OUTPUT_DIR / 'offer_events.csv'}")
    print(f"- {OUTPUT_DIR / 'delayed_rewards.csv'}")
    print(f"Total de eventos gerados: {len(offer_events)}")


if __name__ == "__main__":
    main()
