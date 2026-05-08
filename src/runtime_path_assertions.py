"""
WHY: Runtime path assertions make entry-boundary assumptions executable.
INV: Governance may only be entered through trusted, explicit entry contexts.
SEC: Direct naked Governance invocation fails closed unless an isolated test harness enables
     the compatibility escape hatch for legacy evidence scripts.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

TRUSTED_ENTRY_KIND = "trusted_entry_context"
_ALLOWED_COMPONENTS = {"service_adapter", "test_harness"}
_TEST_COMPAT_ENV = "GATEGRAPH_ALLOW_TEST_DIRECT_GOVERNANCE"


@dataclass(frozen=True)
class TrustedEntryContext:
    kind: str
    source_component: str
    public_entry: bool
    boundary_validated: bool
    runtime_path: str
    direct_governance_call: bool = False

    def as_audit_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source_component": self.source_component,
            "public_entry": self.public_entry,
            "boundary_validated": self.boundary_validated,
            "runtime_path": self.runtime_path,
            "direct_governance_call": self.direct_governance_call,
        }


def service_adapter_context() -> TrustedEntryContext:
    return TrustedEntryContext(
        kind=TRUSTED_ENTRY_KIND,
        source_component="service_adapter",
        public_entry=True,
        boundary_validated=True,
        runtime_path="public_api->service_adapter->governance",
        direct_governance_call=False,
    )


def test_harness_context() -> TrustedEntryContext:
    return TrustedEntryContext(
        kind=TRUSTED_ENTRY_KIND,
        source_component="test_harness",
        public_entry=False,
        boundary_validated=True,
        runtime_path="test_harness->governance",
        direct_governance_call=True,
    )


def _test_compat_enabled() -> bool:
    return os.environ.get(_TEST_COMPAT_ENV) == "1"


def assert_trusted_entry_context(context: TrustedEntryContext | Mapping[str, Any] | None) -> TrustedEntryContext:
    """Fail closed unless Governance receives an explicit trusted entry context.

    The only compatibility exception is an environment-gated test harness path. That
    path is deliberately non-public and exists to keep historical evidence scripts
    focused on their original invariant while new boundary evidence verifies the
    production default blocks naked direct calls.
    """
    if context is None:
        if _test_compat_enabled():
            return test_harness_context()
        raise PermissionError("trusted_entry_context required before governance evaluation")

    if isinstance(context, Mapping):
        try:
            context = TrustedEntryContext(**dict(context))
        except TypeError as exc:
            raise PermissionError(f"invalid trusted_entry_context: {exc}") from exc

    if not isinstance(context, TrustedEntryContext):
        raise PermissionError("trusted_entry_context must be a TrustedEntryContext")
    if context.kind != TRUSTED_ENTRY_KIND:
        raise PermissionError("invalid trusted_entry_context.kind")
    if context.source_component not in _ALLOWED_COMPONENTS:
        raise PermissionError("untrusted source_component for governance entry")
    if not context.boundary_validated:
        raise PermissionError("caller boundary must be validated before governance entry")
    if context.public_entry and context.source_component != "service_adapter":
        raise PermissionError("public governance entry must pass through service_adapter")
    if context.direct_governance_call and not _test_compat_enabled():
        raise PermissionError("direct governance invocation is not a production entry path")
    return context
