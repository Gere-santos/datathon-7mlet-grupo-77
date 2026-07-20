#!/usr/bin/env python3
"""Replay o golden set contra a API HTTP em execução (não contra a política em memória).

Diferente de scripts/run_golden_set.py (que avalia offline, com a política pré-aquecida
por replay no dataset), este script faz requisições HTTP reais para /decide e /reward,
exercitando o contrato da API tal como um cliente externo o veria.

Cada linha de data/golden_set/evaluation_cases.jsonl usa "case_id", não "event_id" —
por isso não pode ser enviada crua para /decide (dá 422). Este script faz a conversão.

Aviso: o servidor iniciado via `make api` sobe com política Thompson Sampling em
cold-start e sem seed fixo, então os casos cujo pass_criteria depende só da amostragem
(ex.: "arm_id == 3") são não-determinísticos — vão variar a cada execução. Os casos que
disparam guardrails (idade < 18, inadimplência + cartão premium, fadiga de contato) e os
casos de erro HTTP são determinísticos e devem sempre passar.

Uso:
    python scripts/replay_golden_set_api.py                       # contra localhost:8000
    python scripts/replay_golden_set_api.py --base-url http://host:8000
    python scripts/replay_golden_set_api.py --output results.json
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
GOLDEN_SET_PATH = ROOT / "data" / "golden_set" / "evaluation_cases.jsonl"
REPORTS_DIR = ROOT / "reports"

ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

INVALID_REWARD_PROBE = 5.0  # fora de [0, 1] — usado para testar a validação de /reward


def _http_json(url: str, payload: dict | None, method: str = "POST") -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8") or "{}")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8") or "{}")
        return exc.code, body


def _eval_criteria(criteria: str, arm_id, decision_id, reward, http_status) -> bool:
    ns = {"arm_id": arm_id, "decision_id": decision_id, "reward": reward, "http_status": http_status}
    try:
        return bool(eval(criteria, {"__builtins__": {}}, ns))  # noqa: S307
    except Exception:
        return False


def _load_cases() -> list[dict]:
    return [
        json.loads(line)
        for line in GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_404_case(base_url: str, case: dict) -> dict:
    event_id = case["context"].get("event_id", "evt_nao_existe")
    status, body = _http_json(f"{base_url}/reward", {"event_id": event_id, "arm_id": 0, "reward": 0.0})
    passed = _eval_criteria(case["pass_criteria"], None, None, None, status)
    return {"http_status": status, "arm_id": None, "reward": None,
            "deterministic": True, "passed": passed, "raw": body}


def _run_reward_validation_case(base_url: str, case: dict) -> dict:
    event_id = f"golden-{case['case_id']}"
    status, body = _http_json(f"{base_url}/decide",
                               {"event_id": event_id, "context": case["context"]})
    if status != 200:
        return {"http_status": status, "arm_id": None, "reward": None,
                "deterministic": True, "passed": False, "raw": body}

    arm_id = body["arm_id"]
    r_status, r_body = _http_json(f"{base_url}/reward",
                                   {"event_id": event_id, "arm_id": arm_id, "reward": INVALID_REWARD_PROBE})
    # reward fora de [0,1] deve ser rejeitado (422) pela validação do Pydantic — nenhum
    # valor inválido chega a ser aplicado, então o "reward" observável continua em [0,1].
    rejected = r_status == 422
    passed = rejected and _eval_criteria(case["pass_criteria"], arm_id, event_id, 0.0, r_status)
    return {"http_status": r_status, "arm_id": arm_id, "reward": None,
            "deterministic": True, "passed": passed,
            "raw": {"decide": body, "reward_attempt": r_body}}


def _run_decide_case(base_url: str, case: dict) -> dict:
    event_id = f"golden-{case['case_id']}"
    subject_key = case["context"].get("subject_key", "golden-set-replay")
    status, body = _http_json(f"{base_url}/decide",
                               {"event_id": event_id, "subject_key": subject_key, "context": case["context"]})
    if status != 200:
        return {"http_status": status, "arm_id": None, "reward": None,
                "deterministic": False, "passed": False, "raw": body}

    arm_id = body["arm_id"]
    guardrail_applied = any(rc.startswith("guardrail_") for rc in body.get("reason_codes", []))
    passed = _eval_criteria(case["pass_criteria"], arm_id, event_id, None, status)
    return {"http_status": status, "arm_id": arm_id, "reward": None,
            "deterministic": guardrail_applied, "passed": passed, "raw": body}


def run_replay(base_url: str) -> dict:
    status, _ = _http_json(f"{base_url}/health", None, method="GET")
    if status != 200:
        print(f"{ANSI_RED}API não respondeu em {base_url}/health (status {status}). "
              f"Suba a API com `make api` antes de rodar este script.{ANSI_RESET}")
        sys.exit(2)

    cases = _load_cases()
    results = []
    for case in cases:
        criteria = case["pass_criteria"]
        if criteria == "http_status == 404":
            outcome = _run_404_case(base_url, case)
        elif criteria.startswith("reward "):
            outcome = _run_reward_validation_case(base_url, case)
        else:
            outcome = _run_decide_case(base_url, case)

        results.append({
            "case_id": case["case_id"],
            "type": case["type"],
            "desc": case["desc"],
            "pass_criteria": criteria,
            **outcome,
        })

    passed = sum(1 for r in results if r["passed"])
    deterministic_total = sum(1 for r in results if r["deterministic"])
    deterministic_passed = sum(1 for r in results if r["deterministic"] and r["passed"])

    return {
        "base_url": base_url,
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "deterministic_total": deterministic_total,
        "deterministic_passed": deterministic_passed,
        "results": results,
    }


def _print_report(report: dict) -> None:
    print(f"\n{ANSI_BOLD}{'=' * 70}{ANSI_RESET}")
    print(f"{ANSI_BOLD}  GOLDEN SET REPLAY — via API HTTP ({report['base_url']}){ANSI_RESET}")
    print(f"{'=' * 70}\n")

    for r in report["results"]:
        icon = f"{ANSI_GREEN}✅ PASS{ANSI_RESET}" if r["passed"] else f"{ANSI_RED}❌ FAIL{ANSI_RESET}"
        tag = "" if r["deterministic"] else f" {ANSI_DIM}[amostragem — não-determinístico]{ANSI_RESET}"
        print(f"  {icon}  {r['case_id']:8s} arm={str(r['arm_id']):>4s} http={r['http_status']}  "
              f"{r['pass_criteria']!r}{tag}")
        if not r["passed"]:
            print(f"         ↳ {r['desc']}")

    print(f"\n{'=' * 70}")
    print(f"  Total: {report['passed']}/{report['total']} passando")
    print(f"  Determinísticos (guardrails + erros HTTP): "
          f"{report['deterministic_passed']}/{report['deterministic_total']}")
    print(f"  {ANSI_YELLOW}Os demais dependem da amostragem do Thompson Sampling em cold-start "
          f"e variam a cada execução — use scripts/run_golden_set.py para avaliação offline "
          f"determinística.{ANSI_RESET}")
    print(f"{'=' * 70}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay do golden set contra a API HTTP")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", default=None, help="Caminho para salvar o JSON de resultados")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    report = run_replay(args.base_url)
    if not args.quiet:
        _print_report(report)

    output_path = Path(args.output) if args.output else REPORTS_DIR / "golden_set_api_results.json"
    REPORTS_DIR.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Relatório salvo em: {output_path}")

    return 0 if report["deterministic_passed"] == report["deterministic_total"] else 1


if __name__ == "__main__":
    sys.exit(main())
