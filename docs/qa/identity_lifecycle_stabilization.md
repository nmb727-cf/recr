# Identity Lifecycle Stabilization QA

Date: 2026-04-08

## 1) Audit Summary

### Safe flows
- Candidate self-registration creates user account and now resolves/creates candidate via shared resolver in auth layer.
- Job apply path for authenticated users now resolves candidate through a canonical helper (`_get_or_create_candidate_for_user` delegates to resolver).

### Inconsistent / duplicate-prone flows (before fix)
- Company add candidate used endpoint-local matching and could branch into duplicate behavior or return conflicts without canonical reuse.
- Agency submit candidate had module-local copy/create behavior and profile copy logic separate from other flows.
- Invite/public apply path had ad hoc create/update behavior outside a global resolver.
- Passport import/link and passport sync used local matching/linking patterns not guaranteed to align with auth/jobs/candidates flows.
- Downstream application create path accepted candidate_id without hard existence guard, allowing fragile downstream assumptions.

### Sequencing weaknesses (before fix)
- Some flows deferred robust candidate identity resolution until later side effects.
- Candidate core profile creation/linking was not uniformly guaranteed before downstream records relied on candidate identity.

### Downstream reliability risks (before fix)
- Identity drift across modules could weaken search/pipeline/matching/intelligence due to split identities.
- Localized matching logic increased chance of inconsistent candidate references.

## 2) Old Lifecycle Problems

- Candidate resolution logic duplicated across Auth, Candidates, Jobs, Agencies, and Passport.
- Resolution keys and create/link behavior were not centrally enforced.
- Tenant association and candidate core identity handling could diverge by module.
- Event semantics for candidate lifecycle were incomplete and inconsistent.

## 3) New Canonical Lifecycle Model

Candidate is global; tenant access is explicit association.

### Self-signup candidate
1. Create user account.
2. Resolve candidate by strong identity keys (user/email/phone/passport where applicable).
3. Create candidate if missing.
4. Link user to candidate.
5. Ensure profile readiness.

### Company-created candidate
1. Resolve existing candidate first using canonical keys.
2. Create only if no safe match.
3. Ensure explicit tenant association (`shared` right + optional visibility engagement).
4. Merge only blank/non-protected fields conservatively.

### Agency-created/submitted candidate
1. Resolve globally first.
2. Create only when no safe match.
3. Add tenant association without changing candidate ownership semantics.
4. Enrich profile conservatively.

### Invite-link candidate
1. Resolve candidate during invite/apply action.
2. Reuse canonical candidate when identity keys match.
3. Avoid ad hoc shadow candidate creation.

### Passport-linked candidate
1. Resolve candidate by explicit link keys and identity keys.
2. Reuse candidate when found; create only if missing.
3. Keep passport linkage on canonical candidate.

## 4) Shared Candidate Resolver

Implemented/hardened in `backend/apps/candidates/identity_service.py`.

Core API:
- `resolve_candidate_identity(...)`
- `ensure_tenant_association(...)`
- `ensure_candidate_profile(...)`
- `merge_candidate_payload(...)`

Behavior:
- Normalizes identity inputs (email/phone).
- Resolves by user link, passport link, then identity keys.
- Creates candidate only when explicitly allowed.
- Links user to candidate safely.
- Ensures tenant association separately from core identity.
- Emits lifecycle events and timeline records with tenant safety guards.

## 5) Tenant Association Handling

- Candidate remains global entity.
- Tenant access/relationship represented through explicit association (`CandidateTenantRight`, `relationship_type='shared'`) and optional visibility engagement.
- Same candidate can be associated with multiple tenants.
- No flow mutates candidate into tenant-owned architecture.

## 6) Downstream Integration Impact

Patched modules to use canonical resolver:
- Auth registration
- Candidate add flows
- Invite/public apply flows
- Jobs candidate resolution for apply paths
- Agency submission flow
- Passport link/import/sync flow
- Pipeline application create now guards candidate existence

Outcome:
- Downstream modules depend on stable candidate identity instead of module-local lazy creation.

## 7) Dedup / Merge Safety

- Conservative matching: prefer explicit link keys and normalized strong keys.
- Conservative merge: blank-field enrichment only unless explicitly overwritten.
- No aggressive weak-signal over-merge introduced.
- Duplicate risk reduced at creation entry points by mandatory resolve-first behavior.

## 8) Tests Added

File:
- `backend/apps/candidates/tests/test_identity_lifecycle_stabilization.py`

Coverage:
1. self-signup creates/links stable candidate identity
2. company add reuses existing candidate
3. agency add reuses existing candidate
4. invite-link flow does not duplicate
5. application resolution uses canonical candidate
6. tenant associations remain explicit/correct
7. conservative dedup avoids weak over-merge

Execution:
- `./venv/bin/python -m pytest backend/apps/candidates/tests/test_identity_lifecycle_stabilization.py -q`
- Result: `7 passed in 79.94s`

## 9) Deferred Items / Remaining Risks

- Integer-to-UUID tenant identifier normalization exists in some paths; this is compatible but indicates historical mixed tenant-ID usage.
- Full backfill/reconciliation of any pre-existing duplicate candidates is out of scope for this stabilization pass.
- Additional end-to-end tests across broader modules (notifications/analytics/audit consumers) are recommended to validate event consumers against new lifecycle events.
