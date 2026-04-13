import re
import uuid

from django.db import migrations
from django.db.models import Q


BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_PREFIX = "SYS"
REF_RE = re.compile(r"^([A-Z0-9]+)-([A-Z]{2})-([0-9A-Z]+)/([0-9]{2})$")


def to_base36(value: int) -> str:
    if value <= 0:
        return "0"
    chars = []
    num = value
    while num:
        num, rem = divmod(num, 36)
        chars.append(BASE36[rem])
    return ''.join(reversed(chars))


def from_base36(raw: str) -> int:
    total = 0
    for ch in (raw or '').upper():
        total = total * 36 + BASE36.index(ch)
    return total


def normalize_prefix(raw: str) -> str:
    value = re.sub(r"[^A-Z0-9]", "", (raw or '').strip().upper())
    return value[:12]


def candidate_type_code(row, tenant_type_map):
    source = (row.get('source') or '').lower()
    source_type = (row.get('source_type') or '').lower()
    entry_type = (row.get('initial_entry_type') or '').lower()
    tenant_id = row.get('tenant_id') or row.get('owner_tenant_id')

    if source in {'self', 'invite_link'} or entry_type in {'self', 'invite'}:
        return 'DC'
    if tenant_id is None:
        return 'DC'
    if source == 'agency' or source_type == 'agency' or entry_type in {'agency_submission', 'agency_submit'}:
        return 'AC'
    if tenant_type_map.get(str(tenant_id)) == 'agency':
        return 'AC'
    return 'CC'


def job_type_code(row, tenant_type_map):
    return 'AJ' if tenant_type_map.get(str(row.get('tenant_id'))) == 'agency' else 'CJ'


def backfill_forward(apps, schema_editor):
    Client = apps.get_model('tenants', 'Client')
    Candidate = apps.get_model('candidates', 'Candidate')
    JobRequisition = apps.get_model('jobs', 'JobRequisition')
    TenantReferenceSequence = apps.get_model('tenants', 'TenantReferenceSequence')

    clients = list(Client.objects.all().values('id', 'name', 'slug', 'tenant_type', 'reference_prefix_auto', 'reference_prefix_custom'))
    if not clients:
        return

    client_ids = [c['id'] for c in clients]
    tenant_type_map = {str(c['id']): c['tenant_type'] for c in clients}

    used_prefixes = set()
    for row in clients:
        if row['reference_prefix_auto']:
            used_prefixes.add(normalize_prefix(row['reference_prefix_auto']))

    def make_auto_prefix(row):
        base = normalize_prefix(((row.get('slug') or row.get('name') or DEFAULT_PREFIX)[:8]))[:8]
        if not base:
            base = DEFAULT_PREFIX
        candidate = base[:8]
        idx = 0
        while not candidate or candidate in used_prefixes:
            idx += 1
            suffix = to_base36(idx)
            keep = max(1, 8 - len(suffix))
            candidate = f"{base[:keep]}{suffix}"
        used_prefixes.add(candidate)
        return candidate

    prefix_by_tenant = {}
    for row in clients:
        auto = normalize_prefix(row.get('reference_prefix_auto') or '')
        custom = normalize_prefix(row.get('reference_prefix_custom') or '')
        if not auto:
            auto = make_auto_prefix(row)
        Client.objects.filter(id=row['id']).update(
            reference_prefix_auto=auto,
            reference_prefix_custom=custom,
        )
        prefix_by_tenant[str(row['id'])] = custom or auto or DEFAULT_PREFIX

    public_client = Client.objects.filter(schema_name='public').values('id').first()
    fallback_tenant_id = public_client['id'] if public_client else client_ids[0]

    counters = {}

    existing_candidates = Candidate.objects.exclude(candidate_ref_id='').exclude(candidate_ref_id__isnull=True).values(
        'tenant_id', 'owner_tenant_id', 'candidate_ref_id'
    )
    for row in existing_candidates:
        tenant_id = row.get('tenant_id') or row.get('owner_tenant_id') or fallback_tenant_id
        raw = row.get('candidate_ref_id') or ''
        match = REF_RE.match(raw)
        if not match:
            continue
        ref_prefix, entity_type, base36_seq, year_suffix = match.groups()
        # Key by prefix extracted from the existing ref_id to stay consistent
        counter_key = (ref_prefix, entity_type, year_suffix)
        counters[counter_key] = max(counters.get(counter_key, 0), from_base36(base36_seq))

    existing_jobs = JobRequisition.objects.exclude(job_ref_id='').exclude(job_ref_id__isnull=True).values(
        'tenant_id', 'job_ref_id'
    )
    for row in existing_jobs:
        raw = row.get('job_ref_id') or ''
        match = REF_RE.match(raw)
        if not match:
            continue
        ref_prefix, entity_type, base36_seq, year_suffix = match.groups()
        counter_key = (ref_prefix, entity_type, year_suffix)
        counters[counter_key] = max(counters.get(counter_key, 0), from_base36(base36_seq))

    missing_candidates = Candidate.objects.filter(Q(candidate_ref_id='') | Q(candidate_ref_id__isnull=True)).values(
        'id', 'tenant_id', 'owner_tenant_id', 'source', 'source_type', 'initial_entry_type', 'created_at'
    )
    for row in missing_candidates.iterator(chunk_size=500):
        tenant_id = row.get('tenant_id') or row.get('owner_tenant_id') or fallback_tenant_id
        tenant_key = str(tenant_id)
        entity_type = candidate_type_code(row, tenant_type_map)
        created_at = row.get('created_at')
        year_suffix = f"{(created_at.year if created_at else 2000) % 100:02d}"
        prefix = prefix_by_tenant.get(tenant_key) or DEFAULT_PREFIX
        # Key by prefix (not tenant) to prevent same-prefix tenants from generating duplicate ref_ids
        counter_key = (prefix, entity_type, year_suffix)
        next_value = counters.get(counter_key, 0) + 1
        counters[counter_key] = next_value
        ref = f"{prefix}-{entity_type}-{to_base36(next_value).rjust(4, '0')}/{year_suffix}"
        Candidate.objects.filter(id=row['id']).update(candidate_ref_id=ref)

    missing_jobs = JobRequisition.objects.filter(Q(job_ref_id='') | Q(job_ref_id__isnull=True)).values(
        'id', 'tenant_id', 'created_at'
    )
    for row in missing_jobs.iterator(chunk_size=500):
        tenant_id = row.get('tenant_id') or fallback_tenant_id
        tenant_key = str(tenant_id)
        entity_type = job_type_code(row, tenant_type_map)
        created_at = row.get('created_at')
        year_suffix = f"{(created_at.year if created_at else 2000) % 100:02d}"
        prefix = prefix_by_tenant.get(tenant_key) or DEFAULT_PREFIX
        # Key by prefix (not tenant) to prevent same-prefix tenants from generating duplicate ref_ids
        counter_key = (prefix, entity_type, year_suffix)
        next_value = counters.get(counter_key, 0) + 1
        counters[counter_key] = next_value
        ref = f"{prefix}-{entity_type}-{to_base36(next_value).rjust(4, '0')}/{year_suffix}"
        JobRequisition.objects.filter(id=row['id']).update(job_ref_id=ref)

    for (tenant_key, entity_type, year_suffix), next_value in counters.items():
        try:
            tenant_uuid = uuid.UUID(str(tenant_key))
        except Exception:
            continue
        seq, _ = TenantReferenceSequence.objects.get_or_create(
            tenant_id=tenant_uuid,
            entity_type=entity_type,
            year_suffix=year_suffix,
            defaults={'next_value': 0},
        )
        if seq.next_value < next_value:
            seq.next_value = next_value
            seq.save(update_fields=['next_value', 'updated_at'])


def backfill_reverse(apps, schema_editor):
    # Keep generated references immutable even on rollback.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_client_reference_prefix_and_sequence'),
        ('candidates', '0018_candidate_candidate_ref_id'),
        ('jobs', '0004_jobrequisition_job_ref_id'),
    ]

    operations = [
        migrations.RunPython(backfill_forward, backfill_reverse),
    ]
