"""
WHY: Multi-agent delegation must be observable without becoming implicit authority.
INV: This module is detection-only; it never grants capabilities, budgets or tool access.
SEC: Delegation chains that imply transitive authority, circular delegation or missing attribution fail closed.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

MAX_DELEGATION_DEPTH = 3
ALLOWED_DELEGATION_MODES = {"reference_only", "proposal_only", "human_review_required"}

@dataclass(frozen=True)
class DelegationEdge:
    from_actor: str
    to_actor: str
    task_id: str
    mode: str = "reference_only"
    requested_capabilities: tuple[str, ...] = ()

@dataclass(frozen=True)
class DelegationAssessment:
    decision: str
    reason: str
    actor_chain: tuple[str, ...]
    delegation_depth: int
    transitive_authority: bool
    circular_delegation: bool
    capability_amplification: bool
    evidence_mode: str = "delegation_boundary_detection_only"
    def to_dict(self) -> dict:
        return asdict(self)

def _valid_actor(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip()) and ":" not in value and "\n" not in value

def assess_delegation_chain(edges: Sequence[DelegationEdge], *, max_depth: int = MAX_DELEGATION_DEPTH) -> DelegationAssessment:
    if not edges:
        return DelegationAssessment("continue", "DELEGATION_EMPTY_CHAIN", (), 0, False, False, False)
    if max_depth < 1:
        return DelegationAssessment("stop", "DELEGATION_INVALID_MAX_DEPTH", (), 0, False, False, False)
    actors: list[str] = []
    requested: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    circular = False
    previous_to: str | None = None
    for index, edge in enumerate(edges):
        if not (_valid_actor(edge.from_actor) and _valid_actor(edge.to_actor) and isinstance(edge.task_id, str) and edge.task_id.strip()):
            return DelegationAssessment("stop", "DELEGATION_INVALID_ATTRIBUTION", tuple(actors), len(edges), False, False, False)
        if edge.mode not in ALLOWED_DELEGATION_MODES:
            return DelegationAssessment("stop", "DELEGATION_UNSUPPORTED_MODE", tuple(actors), len(edges), False, False, False)
        if previous_to is not None and edge.from_actor != previous_to:
            return DelegationAssessment("stop", "DELEGATION_BROKEN_ACTOR_CHAIN", tuple(actors), len(edges), False, False, False)
        pair = (edge.from_actor, edge.to_actor)
        if pair in seen_pairs or edge.to_actor in actors or edge.from_actor == edge.to_actor:
            circular = True
        seen_pairs.add(pair)
        if index == 0:
            actors.append(edge.from_actor)
        actors.append(edge.to_actor)
        requested.update(edge.requested_capabilities)
        previous_to = edge.to_actor
    depth = len(edges)
    transitive_authority = depth > 1
    capability_amplification = bool(requested)
    if depth > max_depth:
        return DelegationAssessment("stop", "DELEGATION_DEPTH_LIMIT", tuple(actors), depth, transitive_authority, circular, capability_amplification)
    if circular:
        return DelegationAssessment("stop", "DELEGATION_CIRCULAR_CHAIN", tuple(actors), depth, transitive_authority, circular, capability_amplification)
    if capability_amplification:
        return DelegationAssessment("stop", "DELEGATION_CAPABILITY_AMPLIFICATION", tuple(actors), depth, transitive_authority, circular, capability_amplification)
    if transitive_authority:
        return DelegationAssessment("stop", "DELEGATION_TRANSITIVE_AUTHORITY_BLOCKED", tuple(actors), depth, transitive_authority, circular, capability_amplification)
    return DelegationAssessment("continue", "DELEGATION_REFERENCE_ONLY", tuple(actors), depth, False, False, False)

def summarize_delegation(edges: Iterable[DelegationEdge]) -> dict:
    return assess_delegation_chain(tuple(edges)).to_dict()
