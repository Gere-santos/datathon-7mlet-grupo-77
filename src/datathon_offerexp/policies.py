from __future__ import annotations

import random
from abc import ABC, abstractmethod

import numpy as np

OFFER_CATALOG: list[dict] = [
    {"arm_id": 0, "arm_name": "sem_oferta"},
    {"arm_id": 1, "arm_name": "educacao_financeira"},
    {"arm_id": 2, "arm_name": "simulador_credito"},
    {"arm_id": 3, "arm_name": "cartao_premium"},
]


class BasePolicy(ABC):
    version: str = "base"

    def __init__(self, arms: list[dict] | None = None) -> None:
        self.arms = arms or OFFER_CATALOG
        self.n_arms = len(self.arms)
        self.trials = [0] * self.n_arms
        self.successes = [0] * self.n_arms

    @abstractmethod
    def select_arm(self) -> int:
        ...

    def update(self, arm_id: int, reward: float) -> None:
        self.trials[arm_id] += 1
        self.successes[arm_id] += int(reward)

    def reward_rates(self) -> list[float]:
        return [
            self.successes[i] / self.trials[i] if self.trials[i] > 0 else 0.0
            for i in range(self.n_arms)
        ]

    def stats(self) -> list[dict]:
        rates = self.reward_rates()
        return [
            {
                "arm_id": a["arm_id"],
                "arm_name": a["arm_name"],
                "trials": self.trials[i],
                "successes": self.successes[i],
                "reward_rate": round(rates[i], 4),
            }
            for i, a in enumerate(self.arms)
        ]


class RandomPolicy(BasePolicy):
    version = "random-v1"

    def select_arm(self) -> int:
        return random.randint(0, self.n_arms - 1)


class GreedyPolicy(BasePolicy):
    """Always selects the arm with the highest observed reward rate.
    Breaks ties by choosing the arm with fewer trials (optimistic tie-breaking).
    """
    version = "greedy-v1"

    def select_arm(self) -> int:
        rates = self.reward_rates()
        # Among arms with equal rates, prefer the less-explored one
        best_rate = max(rates)
        candidates = [i for i, r in enumerate(rates) if r == best_rate]
        return min(candidates, key=lambda i: self.trials[i])


class ThompsonSamplingPolicy(BasePolicy):
    """Thompson Sampling using Beta(alpha, beta) conjugate prior for Bernoulli rewards."""
    version = "thompson-v1"

    def __init__(self, arms: list[dict] | None = None, seed: int | None = None) -> None:
        super().__init__(arms)
        self._rng = np.random.default_rng(seed)

    def select_arm(self) -> int:
        samples = [
            self._rng.beta(self.successes[i] + 1, self.trials[i] - self.successes[i] + 1)
            for i in range(self.n_arms)
        ]
        return int(np.argmax(samples))

    def stats(self) -> list[dict]:
        base = super().stats()
        for i, s in enumerate(base):
            s["alpha"] = self.successes[i] + 1
            s["beta"] = self.trials[i] - self.successes[i] + 1
        return base
