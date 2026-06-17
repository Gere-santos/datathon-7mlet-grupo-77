"""
Evidências de aceite — Etapa 3

Verifica via `make test`:
1. Comparação quantitativa: Thompson Sampling supera o baseline Random em
   reward médio e regret acumulado no mesmo dataset sintético.
2. Justificativa do algoritmo: Thompson converge para o melhor braço;
   Greedy e Random não convergem com a mesma consistência.
3. Cold-start: prior Beta(1,1) garante exploração uniforme antes de qualquer
   observação — nenhum braço é excluído na inicialização.
4. Delayed rewards: a API aceita rewards com atraso via _pending dict;
   o update só ocorre quando o reward chega, não na decisão.
"""

from pathlib import Path

import pandas as pd
import pytest

from datathon_offerexp.evaluation import compute_regret, replay_evaluate, summarize
from datathon_offerexp.policies import (
    GreedyPolicy,
    RandomPolicy,
    ThompsonSamplingPolicy,
)

_EVENTS_PATH = Path(__file__).parents[1] / "data" / "synthetic_enrichment" / "offer_events.csv"
_SEED = 42


def _make_events(n: int, best_arm: int = 3, best_rate: float = 0.40,
                 other_rate: float = 0.10, seed: int = 0) -> pd.DataFrame:
    """Dataset sintético com vencedor claro — usado nos testes de mecanismo.

    O dataset real tem taxas muito próximas (~11% em todos os braços), o que
    impossibilita verificar convergência em amostras pequenas. Aqui usamos
    best_rate=40% vs other_rate=10% para que Thompson convirja visivelmente.
    Os eventos são gerados com logging uniforme (hipótese do Replayer Method).
    """
    import numpy as np
    rng = numpy_rng = __import__("numpy").random.default_rng(seed)
    rows = []
    arm_names = {0: "sem_oferta", 1: "educacao_financeira",
                 2: "simulador_credito", 3: "cartao_premium"}
    for i in range(n):
        arm = int(rng.integers(0, 4))
        rate = best_rate if arm == best_arm else other_rate
        reward = int(rng.random() < rate)
        rows.append({"event_id": f"t_{i}", "arm_id": arm,
                     "arm_name": arm_names[arm], "reward": reward})
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def clear_events() -> pd.DataFrame:
    """Dataset sintético com braço 3 claramente superior (40% vs 10%)."""
    return _make_events(n=10_000, best_arm=3, best_rate=0.40, other_rate=0.10)


@pytest.fixture(scope="module")
def real_events() -> pd.DataFrame:
    """Amostra do dataset real — usado para sanity-check do replayer."""
    return pd.read_csv(_EVENTS_PATH, nrows=5_000)


# ── 1. Comparação quantitativa (dados sintéticos com vencedor claro) ──────────

def test_thompson_supera_random_com_vencedor_claro(clear_events):
    """Thompson deve superar Random quando há braço claramente melhor (40% vs 10%).

    Nota: no dataset real as taxas são quase idênticas (~11% em todos os braços),
    tornando a diferença estatisticamente irrelevante em amostras pequenas.
    A comparação quantitativa completa está nos Notebooks 03, 04 e 07.
    """
    best_rate = 0.40
    df_random   = compute_regret(replay_evaluate(RandomPolicy(), clear_events, seed=_SEED), best_rate)
    df_thompson = compute_regret(replay_evaluate(ThompsonSamplingPolicy(seed=_SEED), clear_events, seed=_SEED), best_rate)

    r_random   = summarize(df_random,   "Random")["avg_reward"]
    r_thompson = summarize(df_thompson, "Thompson")["avg_reward"]

    assert r_thompson > r_random, (
        f"Thompson ({r_thompson:.4f}) deve superar Random ({r_random:.4f}) "
        "quando há braço claramente melhor"
    )
    assert df_thompson["cumulative_regret"].iloc[-1] < df_random["cumulative_regret"].iloc[-1]


def test_tabela_comparativa_tres_politicas(clear_events):
    """Thompson supera Random; Greedy pode ficar abaixo de Random por convergência
    prematura — o que justifica escolher Thompson como política principal."""
    results = {}
    for name, policy in [
        ("Random",   RandomPolicy()),
        ("Greedy",   GreedyPolicy()),
        ("Thompson", ThompsonSamplingPolicy(seed=_SEED)),
    ]:
        df = replay_evaluate(policy, clear_events, seed=_SEED)
        results[name] = summarize(df, name)

    # Thompson deve superar Random quando há braço claramente melhor
    assert results["Thompson"]["avg_reward"] > results["Random"]["avg_reward"], (
        "Thompson deve superar Random com braço 3 a 40% vs outros a 10%"
    )

    # Todas as políticas devem produzir rounds válidos
    for name, r in results.items():
        assert r["rounds"] >= 1_000, f"{name}: rounds insuficientes ({r['rounds']})"

    # Greedy pode falhar por convergência prematura — isso é esperado e documentado
    # (ver test_greedy_trava_apos_convergencia_prematura e relatorio-tecnico.md seção 4.3)


def test_replayer_roda_no_dataset_real(real_events):
    """Sanity-check: as três políticas executam no dataset real sem erros
    e produzem pelo menos 500 rounds cada (Replayer filtra ~1/4 dos eventos)."""
    for name, policy in [
        ("Random",   RandomPolicy()),
        ("Greedy",   GreedyPolicy()),
        ("Thompson", ThompsonSamplingPolicy(seed=_SEED)),
    ]:
        df = replay_evaluate(policy, real_events, seed=_SEED)
        s  = summarize(df, name)
        assert s["rounds"] >= 500, f"{name}: apenas {s['rounds']} rounds no dataset real"
        assert 0.0 < s["avg_reward"] < 1.0


# ── 2. Justificativa do algoritmo — convergência ──────────────────────────────

def test_thompson_concentra_selecoes_no_melhor_braco():
    """Após muitas observações, Thompson deve escolher o melhor braço >50% das vezes."""
    policy = ThompsonSamplingPolicy(seed=_SEED)

    # Braço 3 tem taxa de conversão claramente superior
    for _ in range(300):
        policy.update(3, 1.0)   # ~33% de sucesso simulado no melhor braço
        policy.update(3, 0.0)
        policy.update(3, 0.0)
    for _ in range(100):
        for arm in [0, 1, 2]:  # outros braços têm taxa ~10%
            policy.update(arm, 1.0)
            for _ in range(9):
                policy.update(arm, 0.0)

    selections = [policy.select_arm() for _ in range(200)]
    pct_best = selections.count(3) / len(selections)

    assert pct_best > 0.50, (
        f"Thompson deveria selecionar braço 3 em >50% após convergência, mas selecionou {pct_best:.0%}"
    )


def test_greedy_trava_apos_convergencia_prematura():
    """Greedy trava no primeiro braço que recebe recompensa — não explora os demais."""
    policy = GreedyPolicy()
    policy.update(0, 1.0)   # braço 0 recebe uma conversão inicial

    # Após 50 rodadas sem mais atualizações, Greedy continua escolhendo braço 0
    selections = {policy.select_arm() for _ in range(50)}
    assert 0 in selections
    assert len(selections) == 1, "Greedy não deve explorar após ter uma taxa positiva"


# ── 3. Cold-start ─────────────────────────────────────────────────────────────

def test_cold_start_thompson_explora_todos_os_bracos():
    """No cold-start (zero observações), Thompson com prior Beta(1,1) deve
    selecionar todos os braços ao longo de múltiplas rodadas."""
    policy = ThompsonSamplingPolicy(seed=0)
    selections = {policy.select_arm() for _ in range(40)}
    assert selections == {0, 1, 2, 3}, (
        f"Cold-start deve cobrir todos os braços, mas selecionou apenas: {selections}"
    )


def test_cold_start_prior_uniforme():
    """Beta(1,1) é distribuição uniforme — alpha e beta iniciais devem ser 1."""
    policy = ThompsonSamplingPolicy()
    for s in policy.stats():
        assert s["alpha"] == 1, f"alpha inicial de {s['arm_name']} deve ser 1"
        assert s["beta"]  == 1, f"beta inicial de {s['arm_name']} deve ser 1"


def test_cold_start_greedy_nao_trava_sem_dados():
    """Greedy no cold-start (todas taxas=0) deve explorar por desempate,
    não travar no braço 0."""
    policy = GreedyPolicy()
    selections = set()
    for _ in range(20):
        arm = policy.select_arm()
        selections.add(arm)
        policy.update(arm, 0.0)   # todas não-conversões — desempate por menor trials
    assert len(selections) > 1, "Greedy deve desempatar pelo braço menos explorado"


# ── 4. Delayed rewards ────────────────────────────────────────────────────────

def test_delayed_reward_update_apenas_na_chegada():
    """A política só deve ser atualizada quando o reward chega — não na decisão.
    Simula o mecanismo _pending da API: decide → reward chega depois."""
    policy = ThompsonSamplingPolicy(seed=_SEED)

    # Estado inicial
    alpha_antes = [s["alpha"] for s in policy.stats()]
    beta_antes  = [s["beta"]  for s in policy.stats()]

    # Passo 1: decisão (equivalente ao POST /decide)
    arm = policy.select_arm()
    pending = {arm: arm}  # simula _pending[event_id] = arm_id

    # Estado não deve mudar após a decisão
    assert [s["alpha"] for s in policy.stats()] == alpha_antes
    assert [s["beta"]  for s in policy.stats()] == beta_antes

    # Passo 2: reward chega depois (equivalente ao POST /reward)
    policy.update(pending[arm], 1.0)

    # Agora o estado deve ter mudado apenas no braço selecionado
    alpha_depois = [s["alpha"] for s in policy.stats()]
    assert alpha_depois[arm] == alpha_antes[arm] + 1, "alpha deve incrementar só após reward"
    assert all(
        alpha_depois[i] == alpha_antes[i]
        for i in range(policy.n_arms) if i != arm
    ), "outros braços não devem ser afetados"


def test_delayed_reward_multiplos_pendentes():
    """Múltiplas decisões podem ficar pendentes antes de qualquer reward chegar."""
    policy = ThompsonSamplingPolicy(seed=_SEED)
    pending: dict[str, int] = {}

    # 5 decisões consecutivas sem reward
    for i in range(5):
        arm = policy.select_arm()
        pending[f"evt_{i:03d}"] = arm

    assert len(pending) == 5

    # Rewards chegam fora de ordem (simulando atraso)
    for event_id in reversed(list(pending.keys())):
        arm = pending.pop(event_id)
        policy.update(arm, 1.0)

    assert len(pending) == 0
    total_trials = sum(s["trials"] for s in policy.stats())
    assert total_trials == 5
