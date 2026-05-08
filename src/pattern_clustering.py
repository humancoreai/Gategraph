"""
WHY: Pattern clustering compresses repeated advisory proposals into reviewer-friendly groups.
INV: clustering is read-only; it never changes rules, policies, budgets, secrets, tokens, or actions.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Tuple


_PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def cluster_pattern_proposals(proposals: Iterable[Any]) -> List[Dict[str, Any]]:
    """
    Groups proposal-like objects by proposal_type + inferred target.

    The input may contain PatternProposal dataclasses or dictionaries. The output is
    intentionally plain dictionaries so review/UI layers can consume it without
    importing Pattern Engine internals.
    """
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for proposal in proposals:
        item = _as_dict(proposal)
        key = (str(item.get("proposal_type") or "unknown"), _target_for(item))
        grouped.setdefault(key, []).append(item)

    clusters: List[Dict[str, Any]] = []
    for (proposal_type, target), items in grouped.items():
        support = sum(_support_for(item) for item in items)
        scores = [float(item.get("score") or 0.0) for item in items]
        aggregated_score = round(sum(scores) / max(len(scores), 1), 2)
        highest_priority = min((str(item.get("priority") or "P3") for item in items), key=lambda p: _PRIORITY_RANK.get(p, 99))
        proposal_ids = sorted(str(item.get("proposal_id")) for item in items if item.get("proposal_id"))
        cluster_id = _cluster_id(proposal_type, target)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "proposal_type": proposal_type,
                "target": target,
                "proposal_ids": proposal_ids,
                "proposal_count": len(items),
                "combined_support": support,
                "aggregated_score": aggregated_score,
                "priority": highest_priority,
                "representative_examples": _representative_examples(items),
            }
        )

    return sorted(clusters, key=lambda c: (_PRIORITY_RANK.get(c["priority"], 99), -c["aggregated_score"], c["cluster_id"]))


def _as_dict(proposal: Any) -> Dict[str, Any]:
    if is_dataclass(proposal):
        return asdict(proposal)
    if isinstance(proposal, dict):
        return dict(proposal)
    raise TypeError(f"unsupported proposal type: {type(proposal).__name__}")


def _target_for(item: Dict[str, Any]) -> str:
    if item.get("target_rule_id"):
        return str(item["target_rule_id"])
    reason = str(item.get("reason") or "")
    for marker in ("stage=", "capability=", "bucket="):
        if marker not in reason:
            continue
    # Stable enough for advisory clustering: same stage/capability/bucket reason groups together.
    return reason or str(item.get("proposed_change") or "unknown")[:120]


def _support_for(item: Dict[str, Any]) -> int:
    events = item.get("supporting_events") or []
    if isinstance(events, str):
        # Stored rows may contain JSON text; fall back to one supporting item if not decoded here.
        return 1
    try:
        return max(len(events), 1)
    except TypeError:
        return 1


def _representative_examples(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = sorted(items, key=lambda i: (-float(i.get("score") or 0.0), str(i.get("proposal_id") or "")))
    examples = []
    for item in ranked[:3]:
        examples.append(
            {
                "proposal_id": item.get("proposal_id"),
                "priority": item.get("priority"),
                "score": item.get("score"),
                "reason": item.get("reason"),
            }
        )
    return examples


def _cluster_id(proposal_type: str, target: str) -> str:
    digest = hashlib.sha256(f"{proposal_type}|{target}".encode("utf-8")).hexdigest()[:12].upper()
    return f"PCL-{digest}"
