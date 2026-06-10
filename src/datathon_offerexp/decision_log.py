from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


class DecisionLog:
    """Appends decision records as JSONL for audit and replay."""

    def __init__(self, path: str | Path = "decision_log.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event_id: str,
        arm_id: int,
        arm_name: str,
        reward: float | None,
        policy_version: str,
        reason_codes: list[str] | None = None,
    ) -> str:
        decision_id = str(uuid.uuid4())
        record = {
            "decision_id": decision_id,
            "event_id": event_id,
            "policy_version": policy_version,
            "arm_id": arm_id,
            "arm_name": arm_name,
            "reward": reward,
            "reason_codes": reason_codes or [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return decision_id

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        records = []
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
