import re
import uuid
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.tenants.models import Client, TenantReferenceSequence


BASE36_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
REFERENCE_SEQUENCE_WIDTH = 4
DEFAULT_PREFIX = "SYS"
PREFIX_PATTERN = re.compile(r"[^A-Z0-9]")


def _to_base36(value: int) -> str:
    if value <= 0:
        return "0"
    digits = []
    num = value
    while num:
        num, remainder = divmod(num, 36)
        digits.append(BASE36_ALPHABET[remainder])
    return "".join(reversed(digits))


def normalize_prefix(raw: str | None) -> str:
    value = (raw or "").strip().upper()
    value = PREFIX_PATTERN.sub("", value)
    if not value:
        return ""
    return value[:12]


def _tenant_id_or_public(tenant_id):
    if tenant_id:
        return tenant_id
    public = Client.objects.filter(schema_name='public').values('id').first()
    if public:
        return public['id']
    return None


def _get_client_by_tenant_id(tenant_id):
    if not tenant_id:
        return None
    try:
        parsed = uuid.UUID(str(tenant_id))
    except Exception:
        return Client.objects.filter(id=tenant_id).first()
    return Client.objects.filter(id=parsed).first()


def _generate_auto_prefix(client: Client) -> str:
    base = normalize_prefix((client.slug or client.name or DEFAULT_PREFIX)[:8])[:8]
    if not base:
        base = DEFAULT_PREFIX

    candidate = base[:8]
    suffix = 0
    while Client.objects.exclude(id=client.id).filter(reference_prefix_auto=candidate).exists():
        suffix += 1
        encoded = _to_base36(suffix)
        keep = max(1, 8 - len(encoded))
        candidate = f"{base[:keep]}{encoded}"
    return candidate


def ensure_tenant_prefix(tenant_id) -> str:
    resolved_tenant_id = _tenant_id_or_public(tenant_id)
    if not resolved_tenant_id:
        return DEFAULT_PREFIX

    client = _get_client_by_tenant_id(resolved_tenant_id)
    if not client:
        return DEFAULT_PREFIX

    dirty = False
    custom = normalize_prefix(client.reference_prefix_custom)
    auto = normalize_prefix(client.reference_prefix_auto)

    if custom != (client.reference_prefix_custom or ""):
        client.reference_prefix_custom = custom
        dirty = True

    if not auto:
        client.reference_prefix_auto = _generate_auto_prefix(client)
        dirty = True
    elif auto != (client.reference_prefix_auto or ""):
        client.reference_prefix_auto = auto
        dirty = True

    if dirty:
        client.save(update_fields=['reference_prefix_custom', 'reference_prefix_auto'])

    return client.reference_prefix_custom or client.reference_prefix_auto or DEFAULT_PREFIX


def _tenant_type(tenant_id) -> str:
    client = _get_client_by_tenant_id(_tenant_id_or_public(tenant_id))
    if not client:
        return 'company'
    return client.tenant_type


def candidate_type_code(candidate) -> str:
    source = (getattr(candidate, 'source', '') or '').lower()
    source_type = (getattr(candidate, 'source_type', '') or '').lower()
    entry_type = (getattr(candidate, 'initial_entry_type', '') or '').lower()
    tenant_id = getattr(candidate, 'tenant_id', None) or getattr(candidate, 'owner_tenant_id', None)

    if source in {'self', 'invite_link'} or entry_type in {'self', 'invite'}:
        return 'DC'
    if tenant_id is None:
        return 'DC'
    if source == 'agency' or source_type == 'agency' or entry_type in {'agency_submission', 'agency_submit'}:
        return 'AC'
    if _tenant_type(tenant_id) == 'agency':
        return 'AC'
    return 'CC'


def job_type_code(job) -> str:
    return 'AJ' if _tenant_type(getattr(job, 'tenant_id', None)) == 'agency' else 'CJ'


@transaction.atomic
def build_reference(*, tenant_id, entity_type: str, created_at: datetime | None = None) -> str:
    resolved_tenant_id = _tenant_id_or_public(tenant_id)
    if not resolved_tenant_id:
        raise ValueError("Cannot generate reference without tenant context.")

    ts = created_at or timezone.now()
    year_suffix = f"{ts.year % 100:02d}"
    prefix = ensure_tenant_prefix(resolved_tenant_id)

    sequence = TenantReferenceSequence.objects.select_for_update().filter(
        tenant_id=resolved_tenant_id,
        entity_type=entity_type,
        year_suffix=year_suffix,
    ).first()
    if not sequence:
        try:
            sequence = TenantReferenceSequence.objects.create(
                tenant_id=resolved_tenant_id,
                entity_type=entity_type,
                year_suffix=year_suffix,
                next_value=0,
            )
        except IntegrityError:
            sequence = TenantReferenceSequence.objects.select_for_update().get(
                tenant_id=resolved_tenant_id,
                entity_type=entity_type,
                year_suffix=year_suffix,
            )

    sequence.next_value += 1
    sequence.save(update_fields=['next_value', 'updated_at'])

    base36_seq = _to_base36(sequence.next_value).rjust(REFERENCE_SEQUENCE_WIDTH, '0')
    return f"{prefix}-{entity_type}-{base36_seq}/{year_suffix}"
