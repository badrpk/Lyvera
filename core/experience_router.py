from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Dict, Iterable, Mapping


@dataclass(frozen=True)
class Experience:
    name: str
    enabled: bool = True
    rollout_percent: int = 100
    required_traits: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("experience name is required")
        if not 0 <= self.rollout_percent <= 100:
            raise ValueError("rollout_percent must be between 0 and 100")


class ExperienceRouter:
    """Deterministic, privacy-preserving app experience routing.

    The router uses a stable hash of a caller-provided opaque subject ID.
    It does not require analytics, cookies, network access or personal data.
    """

    def __init__(self, experiences: Iterable[Experience] = ()) -> None:
        self._items: Dict[str, Experience] = {}
        for item in experiences:
            self.register(item)

    def register(self, experience: Experience) -> None:
        self._items[experience.name] = experience

    def names(self) -> list[str]:
        return sorted(self._items)

    @staticmethod
    def _bucket(subject_id: str, experience_name: str) -> int:
        if not subject_id:
            raise ValueError("subject_id is required")
        digest = sha256(f"{experience_name}\0{subject_id}".encode()).digest()
        return int.from_bytes(digest[:8], "big") % 100

    def enabled_for(
        self,
        experience_name: str,
        *,
        subject_id: str,
        traits: Iterable[str] = (),
    ) -> bool:
        try:
            item = self._items[experience_name]
        except KeyError as exc:
            raise KeyError(f"unknown experience: {experience_name}") from exc

        if not item.enabled:
            return False

        provided = frozenset(str(x).strip() for x in traits if str(x).strip())
        if not item.required_traits.issubset(provided):
            return False

        if item.rollout_percent == 100:
            return True
        if item.rollout_percent == 0:
            return False
        return self._bucket(subject_id, item.name) < item.rollout_percent

    def route(self, *, subject_id: str, traits: Iterable[str] = ()) -> list[str]:
        return [
            name
            for name in self.names()
            if self.enabled_for(name, subject_id=subject_id, traits=traits)
        ]

    def manifest(self) -> Mapping[str, dict]:
        return {
            name: {
                "enabled": item.enabled,
                "rollout_percent": item.rollout_percent,
                "required_traits": sorted(item.required_traits),
            }
            for name, item in sorted(self._items.items())
        }

    def manifest_hash(self) -> str:
        payload = dumps(self.manifest(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()
