"""
Management command: seed_rbac

Creates or updates all Permission and Role objects from the registry, then
assigns permissions to roles as defined in ROLE_PERMISSION_MAP.

Safe to run multiple times — uses get_or_create / update_or_create throughout.

Usage:
    python manage.py seed_rbac            # normal run
    python manage.py seed_rbac --reset    # drop all role-permission assignments
                                          # and re-apply from scratch
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache

from apps.rbac.models import Permission, Role, RolePermission
from apps.rbac.registry import (
    PERMISSION_REGISTRY,
    ROLE_DEFINITIONS,
    ROLE_PERMISSION_MAP,
    resolve_permission_codes,
)


def _titleize(value: str) -> str:
    return value.replace('_', ' ').replace('.', ' ').strip().title()


MODULE_LABEL_OVERRIDES = {
    'candidates': 'Candidates',
    'jobs': 'Jobs',
    'pipeline': 'Pipeline',
    'interviews': 'Interviews',
    'agencies': 'Agencies',
    'organisations': 'Organisation',
    'analytics': 'Analytics',
    'communications': 'Communications',
}


PERMISSION_LABEL_OVERRIDES = {
    'candidates.candidate.view': 'View Candidates',
    'candidates.candidate.create': 'Create Candidate',
    'candidates.candidate.edit': 'Edit Candidate',
    'candidates.candidate.delete': 'Delete Candidate',
    'candidates.note.create': 'Add Candidate Note',
    'candidates.note.view': 'View Candidate Notes',
    'jobs.job.view': 'View Jobs',
    'jobs.job.create': 'Create Job',
    'jobs.job.edit': 'Edit Job',
    'jobs.job.delete': 'Delete Job',
    'jobs.job.approve': 'Approve / Publish Job',
    'pipeline.application.view': 'View Pipeline',
    'pipeline.application.move_stage': 'Move Candidate Stage',
    'pipeline.application.reject': 'Reject Candidate',
    # Communications
    'communications.email.view': 'View Email History',
    'communications.email.send': 'Send Emails',
    'communication.email_accounts.view': 'View Connected Email Accounts',
    'communication.email_accounts.manage': 'Manage Email Accounts (connect / disconnect)',
    'communication.email_templates.view': 'View Email Templates',
    'communication.email_templates.manage': 'Manage Email Templates',
    'communication.quick_replies.manage': 'Manage Quick Replies',
    'communication.email.send': 'Send Emails (Communication Engine)',
    'communication.email.send_from_shared_account': 'Send from Shared Team Account',
    'communication.email.audit.view': 'View Email Audit Trail',
}


def _build_label(entry: dict) -> str:
    code = entry.get('code', '')
    if code in PERMISSION_LABEL_OVERRIDES:
        return PERMISSION_LABEL_OVERRIDES[code]
    if entry.get('label'):
        return entry['label']
    action = _titleize(entry.get('action', ''))
    resource = _titleize(entry.get('resource', ''))
    if action and resource:
        return f'{action} {resource}'
    return _titleize(entry.get('code', 'permission'))


def _build_module_label(entry: dict) -> str:
    module = entry.get('module', '')
    if module in MODULE_LABEL_OVERRIDES:
        return MODULE_LABEL_OVERRIDES[module]
    if entry.get('module_label'):
        return entry['module_label']
    return _titleize(entry.get('module', 'general'))


class Command(BaseCommand):
    help = 'Seed RBAC permissions and role-permission mappings from the registry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Drop all existing RolePermission rows before re-seeding',
        )

    def handle(self, *args, **options):
        reset = options['reset']

        self.stdout.write(self.style.MIGRATE_HEADING('\n─── RBAC Seed ───\n'))

        # ── 1. Upsert permissions ──────────────────────────────────────────────
        self.stdout.write('  [1/4] Syncing permission catalogue...')
        created_count = updated_count = 0
        perm_map: dict[str, Permission] = {}

        for entry in PERMISSION_REGISTRY:
            perm, created = Permission.objects.update_or_create(
                code=entry['code'],
                defaults={
                    'label': _build_label(entry),
                    'module': entry['module'],
                    'module_label': _build_module_label(entry),
                    'resource': entry['resource'],
                    'action': entry['action'],
                    'description': entry.get('description', ''),
                    'is_active': True,
                },
            )
            perm_map[perm.code] = perm
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f'       {created_count} created, {updated_count} updated '
            f'({len(perm_map)} total)'
        )

        # ── 2. Upsert roles ────────────────────────────────────────────────────
        self.stdout.write('  [2/4] Syncing role definitions...')
        role_map: dict[str, Role] = {}

        for defn in ROLE_DEFINITIONS:
            role, _ = Role.objects.update_or_create(
                name=defn['name'],
                tenant_id=None,  # system roles are tenant-agnostic
                defaults={
                    'display_name': defn['display_name'],
                    'description': defn.get('description', ''),
                    'is_system': True,
                },
            )
            role_map[role.name] = role

        self.stdout.write(f'       {len(role_map)} roles synced')

        # ── 3. Optionally clear existing assignments ───────────────────────────
        if reset:
            self.stdout.write('  [3/4] Resetting role-permission assignments...')
            deleted, _ = RolePermission.objects.filter(
                role__tenant_id__isnull=True
            ).delete()
            self.stdout.write(f'       {deleted} rows deleted')
        else:
            self.stdout.write('  [3/4] Skipping reset (pass --reset to rebuild from scratch)')

        # ── 4. Apply role → permission assignments ─────────────────────────────
        self.stdout.write('  [4/4] Applying role-permission assignments...')
        total_assigned = total_skipped = 0

        for role_name, role in role_map.items():
            codes = resolve_permission_codes(role_name)
            assigned = skipped = 0

            for code in codes:
                perm = perm_map.get(code)
                if perm is None:
                    self.stderr.write(
                        self.style.WARNING(
                            f'       WARNING: permission "{code}" in ROLE_PERMISSION_MAP '
                            f'for role "{role_name}" is not in PERMISSION_REGISTRY — skipped'
                        )
                    )
                    continue
                _, created = RolePermission.objects.get_or_create(
                    role=role, permission=perm
                )
                if created:
                    assigned += 1
                else:
                    skipped += 1

            total_assigned += assigned
            total_skipped += skipped
            self.stdout.write(
                f'       {role_name:20s}  +{assigned:3d} new  {skipped:3d} already set  '
                f'(total: {len(codes)})'
            )

        # ── 5. Bust permission caches ──────────────────────────────────────────
        try:
            cache.clear()
            self.stdout.write('       Permission cache cleared')
        except Exception:
            pass  # cache not configured — fine

        self.stdout.write(self.style.SUCCESS(
            f'\n  Done.  {total_assigned} new assignments, '
            f'{total_skipped} already existed.\n'
        ))
