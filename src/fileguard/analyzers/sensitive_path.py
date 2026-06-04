# -*- coding: utf-8 -*-
"""Sensitive-path policy analyzer."""

from __future__ import annotations

import fnmatch
import logging

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


def _clamp_score(value: float) -> float:
    """Clamp an analyzer score to the common 0.0 to 10.0 range."""
    return max(0.0, min(10.0, value))


class SensitivePathAnalyzer(BaseAnalyzer):
    """Detect events whose paths match configured sensitive policies."""

    @property
    def name(self) -> str:
        """Return the analyzer display name."""
        return "SensitivePathAnalyzer"

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Analyze event paths against configured sensitive path policies."""
        for policy in self.config.get("policies", []):
            if not isinstance(policy, dict):
                continue

            matched = self._match_policy(event, policy)
            if matched is None:
                continue

            matched_path, matched_pattern = matched
            risk_base = float(policy.get("risk_base", 0.0))
            final_value = risk_base
            time_restricted = False

            restriction = policy.get("time_restriction")
            if isinstance(restriction, dict):
                deny_hours = {int(hour) for hour in restriction.get("deny_hours", [])}
                if event.timestamp.hour in deny_hours:
                    time_restricted = True
                    multiplier = float(restriction.get("time_multiplier", 1.0))
                    final_value *= multiplier

            final_value = _clamp_score(final_value)
            evidence = {
                "policy_name": str(policy.get("name", "")),
                "pattern": matched_pattern,
                "matched_path": matched_path,
                "risk_base": risk_base,
                "time_restricted": time_restricted,
                "final_value": final_value,
            }
            logger.info(
                "Sensitive path policy hit: policy=%s path=%s",
                evidence["policy_name"],
                matched_path,
            )
            return self.create_signal("policy_hit", final_value, evidence)

        return None

    def _match_policy(
        self, event: FileEvent, policy: dict
    ) -> tuple[str, str] | None:
        """Return the matched event path and pattern for a policy, if any."""
        raw_pattern = str(policy.get("pattern", ""))
        patterns = [part.strip() for part in raw_pattern.split("|") if part.strip()]
        if not patterns:
            return None

        paths = [event.src_path]
        if event.dest_path:
            paths.append(event.dest_path)

        for candidate in paths:
            normalized_path = self._normalize_path(candidate)
            for pattern in patterns:
                if self._path_matches(normalized_path, pattern):
                    return normalized_path, pattern
        return None

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize a path string for cross-platform glob matching."""
        return path.replace("\\", "/")

    @classmethod
    def _path_matches(cls, normalized_path: str, pattern: str) -> bool:
        """Match a normalized path with Windows/POSIX-friendly glob variants."""
        normalized_pattern = cls._normalize_path(pattern).strip()
        if not normalized_pattern:
            return False

        path_variants = {
            normalized_path,
            normalized_path.lstrip("./"),
        }
        pattern_variants = {
            normalized_pattern,
            normalized_pattern.lstrip("./"),
        }

        if normalized_pattern.startswith("**/"):
            pattern_variants.add(normalized_pattern[3:])
        elif "/" in normalized_pattern:
            pattern_variants.add(f"**/{normalized_pattern}")
            pattern_variants.add(f"*/{normalized_pattern}")

        if "/" not in normalized_pattern:
            path_variants.add(normalized_path.rsplit("/", 1)[-1])

        for path_value in path_variants:
            for pattern_value in pattern_variants:
                if fnmatch.fnmatchcase(path_value, pattern_value):
                    return True
                if fnmatch.fnmatchcase(path_value.lower(), pattern_value.lower()):
                    return True
        return False
