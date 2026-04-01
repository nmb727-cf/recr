"""
Standard owner-module contract primitives.

Template for future bindings:
1. Orchestration builds an `OwnerActionContext`.
2. The owner module exposes a narrow `*_from_orchestration(...)` method.
3. The owner method returns `OwnerActionResult`.
4. Validation and ownership failures raise `OwnerContractError`.
5. The executor serializes the result and keeps failures non-blocking.
"""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class OwnerActionContext:
    tenant_id: Any
    actor_id: Any = None
    external_source: str = 'orchestration_center'
    external_reference: str = ''
    audit_metadata: dict[str, Any] = field(default_factory=dict)

    def metadata_payload(self, **extra: Any) -> dict[str, Any]:
        payload = dict(self.audit_metadata or {})
        payload.setdefault('external_source', self.external_source)
        if self.external_reference:
            payload.setdefault('external_reference', self.external_reference)
        payload.update({key: value for key, value in extra.items() if value is not None})
        return payload


@dataclass(frozen=True)
class OwnerActionResult:
    owner_module: str
    action_family: str
    status: str
    target_type: str
    target_id: str = ''
    duplicate: bool = False
    retry_safe: bool = True
    audit_metadata: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)

    def as_contract_payload(self) -> dict[str, Any]:
        return asdict(self)

    def execution_status(self) -> str:
        return 'deduplicated' if self.duplicate else self.status

    def as_execution_payload(self, *, action_type: str) -> dict[str, Any]:
        payload = {
            'action_type': action_type,
            'status': self.execution_status(),
            'owner_module': self.owner_module,
            'action_family': self.action_family,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'duplicate': self.duplicate,
            'retry_safe': self.retry_safe,
            'audit_metadata': self.audit_metadata,
            'payload': self.payload,
        }
        payload.update(self.payload)
        return payload


class OwnerContractError(ValueError):
    CATEGORY_VALIDATION = 'owner_contract_validation'
    CATEGORY_OWNERSHIP = 'owner_contract_ownership'
    CATEGORY_NOT_FOUND = 'owner_contract_not_found'
    CATEGORY_UNSUPPORTED = 'owner_contract_unsupported'
    CATEGORY_TRANSIENT = 'owner_contract_transient'

    def __init__(self, message: str, *, error_category: str = CATEGORY_VALIDATION, retry_safe: bool = False):
        super().__init__(message)
        self.error_category = error_category
        self.retry_safe = retry_safe

    @classmethod
    def validation(cls, message: str):
        return cls(message, error_category=cls.CATEGORY_VALIDATION, retry_safe=False)

    @classmethod
    def ownership(cls, message: str):
        return cls(message, error_category=cls.CATEGORY_OWNERSHIP, retry_safe=False)

    @classmethod
    def not_found(cls, message: str):
        return cls(message, error_category=cls.CATEGORY_NOT_FOUND, retry_safe=False)

    @classmethod
    def unsupported(cls, message: str):
        return cls(message, error_category=cls.CATEGORY_UNSUPPORTED, retry_safe=False)

    @classmethod
    def transient(cls, message: str):
        return cls(message, error_category=cls.CATEGORY_TRANSIENT, retry_safe=True)
