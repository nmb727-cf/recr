# Communication Search, History, Archive & Retention

**Prompt ID:** COMMS-SEARCH-AND-ARCHIVE-01  
**Module:** Communications Engine — Search & Archive Layer  
**Status:** Complete (Phase 1)

---

## Overview

The Communication Search & Archive layer gives every user operational memory over all communication activity on the platform. It is not just inbox search — it is the full retrieval, audit, and lifecycle management system for messages, threads, and notifications across all entities.

Any permitted user can:
- Find a conversation from months ago with a single keyword
- See the full communication timeline for a candidate or job in one tab
- Archive noisy threads without losing history
- Retrieve notification history filtered by read state, severity, or topic
- Navigate directly to the exact message in a thread that matched a search

All retrieval is strictly permission-gated. No cross-tenant leakage. Internal threads are never exposed to unauthorised roles.

---

## Architecture

### Search Strategy (Phase 1)
PostgreSQL `icontains` on indexed text fields. No external search engine required for Phase 1.

Future path: Meilisearch can be plugged in by replacing the `icontains` queries in `CommunicationSearchService` — the service layer abstracts the backend completely.

### Result Types
Global search returns a unified mixed list with typed entries:

| Type | Source | Navigation |
|------|--------|------------|
| `thread` | MessageThread subject match | Opens thread |
| `message` | Message body match | Opens thread, jumps to message |
| `notification` | Notification title/body match | Follows action_url |

### Access Control
Every query starts with a `ThreadParticipant` lookup scoped to `(user_id, tenant_id)`. No thread data is returned for threads the user is not an active participant of. Internal threads (`is_internal=True`) are protected by this gate.

---

## Key Components

### Models

**`MessageThread`** (existing, extended in migration 0009)
```
is_archived         BooleanField     default=False
archived_at         DateTimeField    nullable
archived_by         UUIDField        nullable
retention_category  CharField        blank — e.g. 'legal', 'compliance', 'standard'
purge_eligible_at   DateTimeField    nullable — future scheduled purge date
legal_hold          BooleanField     default=False — blocks archive + purge
```

**`Notification`** (existing)
```
is_archived   BooleanField   default=False
archived_at   DateTimeField  nullable
```

No new models were introduced for Phase 1. PostgreSQL full-text search is performed natively.

---

### Service: `CommunicationSearchService`

Located at `apps/communications/search_service.py`.

All methods are `@staticmethod` — no instantiation required.

#### `search_communications(...)`
Global search across thread subjects + message bodies + notification titles/bodies.

Key parameters:
```
tenant_id, user_id       — required, enforces isolation
query                    — required, non-empty string
entity_type, entity_id   — narrow to one entity (e.g. candidate)
thread_type              — filter by thread kind
channel_type             — filter by channel (in_app, email, etc.)
message_type             — filter by message type (text, system_event, etc.)
sender_id                — filter by sender
date_from, date_to       — ISO-8601 datetime bounds
include_archived         — default False; True exposes archived threads
limit, offset            — pagination (max 200)
```

Returns:
```json
{
  "results": [
    {
      "type": "message",
      "id": "...",
      "thread_id": "...",
      "title": "Interview Coordination",
      "snippet": "…the candidate John was shortlisted…",
      "matched_field": "body",
      "sent_at": "2026-04-09T10:32:00Z",
      "sender_id": "...",
      "related_entity": {"type": "candidate", "id": "..."},
      "is_archived": false,
      "participants": ["uuid1", "uuid2"],
      "nav_target": "/messages/threads/uuid?message=uuid"
    }
  ],
  "total": 14,
  "limit": 50,
  "offset": 0
}
```

#### `search_thread_messages(...)`
Full-text search within a single thread. Validates participant access first.

Returns results in chronological order with `nav_target` set to the exact message anchor — the frontend can scroll directly to the result.

#### `get_entity_communication_history(...)`
Unified timeline of all communications linked to a specific entity (Candidate, Job, Application, Interview, Offer).

Pulls:
- Messages where `related_entity_type/id` matches, or the message's thread references the entity
- Notifications where `related_entity_type/id` matches

Returns a `timeline` list sorted newest-first. Each item has `type`, `event_at`, `title`, `preview`, and `nav_target`.

#### `archive_thread(...)` / `unarchive_thread(...)`
Archive: requires active participant membership. Blocked by `legal_hold=True`. Idempotent.  
Unarchive: same participant check. Idempotent.

Both operations log at `INFO` level.

#### `get_archived_threads(...)`
Returns all archived threads the user participates in, ordered by `archived_at` descending. Includes `retention_category` and `legal_hold` fields so the UI can surface compliance metadata.

#### `get_recent_communications(...)`
Returns the most recently active threads (not archived, not deleted) with unread message counts. Used for quick-navigation widgets and inbox previews.

#### `get_notification_history(...)`
Filterable notification history:
- `q` — text search on title + body
- `is_read` — True/False/None (all)
- `include_archived` — default True
- `include_expired` — default True
- `severity` — info/medium/high/critical
- `entity_type`, `entity_id` — entity filter

Each returned item includes `is_expired`, `fallback_email_sent`, `fallback_whatsapp_sent`.

#### `check_communication_access(...)`
Reusable gate. Returns `True` if `user_id` is an active participant in the thread within the given tenant. Archived threads pass; deleted threads fail.

#### `build_search_snippet(text, query, radius=120)`
Extracts a context window around the first match position in `text`. Handles:
- Word-boundary trimming
- Ellipsis padding when text is truncated
- Fallback to first word of query when exact phrase not found

---

### Migration: `0011_search_archive_indexes`

13 composite indexes added across three tables.

**MessageThread indexes:**
- `(tenant_id, is_archived, is_deleted, archived_at)` — archived list queries
- `(tenant_id, purge_eligible_at, is_deleted)` — retention pipeline
- `(tenant_id, legal_hold, is_deleted)` — compliance view
- `(tenant_id, related_entity_type, related_entity_id, is_deleted, is_archived)` — entity history
- `(tenant_id, is_deleted, is_archived, last_message_at)` — inbox ordering

**Message indexes:**
- `(thread_id, is_deleted, sent_at)` — thread timeline
- `(tenant_id, related_entity_type, related_entity_id, is_deleted)` — entity history
- `(tenant_id, sender_id, is_deleted, sent_at)` — sender filter
- `(tenant_id, channel_type, message_type, is_deleted)` — channel/type filter

**Notification indexes:**
- `(user_id, is_archived, created_at)` — notification history
- `(user_id, is_read, is_archived, created_at)` — unread filter
- `(user_id, expires_at)` — expiry management
- `(tenant_id, related_entity_type, related_entity_id)` — entity history
- `(tenant_id, severity, is_read)` — severity/compliance view

All `tenant_id`-leading indexes allow the query planner to apply tenant isolation before scanning.

---

## API Endpoints

All endpoints require authentication. Responses follow the project envelope: `{success, data, message}`.

### Global Search
```
GET /api/v1/communications/search/
```
Query params: `q` (required), `entity_type`, `entity_id`, `thread_type`, `channel_type`, `message_type`, `sender_id`, `date_from`, `date_to`, `archived`, `limit`, `offset`

### Thread Search
```
GET /api/v1/messages/threads/{id}/search/
```
Query params: `q` (required), `sender_id`, `message_type`, `date_from`, `date_to`, `limit`, `offset`

### Archive Controls
```
POST /api/v1/messages/threads/{id}/archive/
POST /api/v1/messages/threads/{id}/unarchive/
```

### Archived Threads List
```
GET /api/v1/messages/archived/
```
Query params: `thread_type`, `limit`, `offset`

### Entity Communication History
```
GET /api/v1/communications/history/{entity_type}/{entity_id}/
```
Query params: `limit`, `offset`

Entity types: `candidate`, `job`, `application`, `interview`, `offer`, `agency`

### Recent Communications
```
GET /api/v1/communications/recent/
```
Query params: `limit` (max 50, default 20)

### Notification History
```
GET /api/v1/notifications/history/
```
Query params: `q`, `is_read`, `include_archived`, `include_expired`, `severity`, `entity_type`, `entity_id`, `limit`, `offset`

---

## Business Rules

| Rule | Behaviour |
|------|-----------|
| Tenant isolation | Every query gates on `tenant_id`. Cross-tenant access returns zero results. |
| Participant gate | Internal threads only visible to participants. Non-participants get no data. |
| Agency/candidate split | Internal recruiter threads (`is_internal=True`) invisible to candidates and agency users. |
| Archived = soft cleanup | Archived threads excluded from default results. Still accessible when `archived=true`. |
| Legal hold | `legal_hold=True` blocks archiving. Thread remains in active state until hold is released. |
| No hard deletes | `is_deleted` flag used throughout. Purge pipeline is future work. |
| Search pagination | All endpoints paginated. Maximum 200 results per page. |
| Snippet safety | Snippets are character-truncated context windows, not raw data dumps. |

---

## Frontend Contract

The backend supports the following UI experiences:

| Experience | Endpoint |
|-----------|----------|
| Global communication search bar | `GET /communications/search/` |
| Jump-to-message in thread | `nav_target` in message search result |
| Thread-level search with jump | `GET /messages/threads/{id}/search/` |
| Entity communication history tab | `GET /communications/history/{type}/{id}/` |
| Inbox archive filter | `GET /messages/threads/?is_archived=true` |
| Archived threads drawer | `GET /messages/archived/` |
| Recent communications widget | `GET /communications/recent/` |
| Notification history view | `GET /notifications/history/` |

Every search result includes `nav_target` — a frontend route string the UI can push directly to the router. The format is:
- Thread: `/messages/threads/{thread_id}`
- Message: `/messages/threads/{thread_id}?message={message_id}`
- Notification: the notification's `action_url` field

---

## Retention & Compliance Foundations

Phase 1 lays the data structure for future compliance workflows:

| Field | Purpose | Status |
|-------|---------|--------|
| `retention_category` | Label for data classification (legal, standard, etc.) | Stored, not enforced |
| `purge_eligible_at` | Scheduled date when thread may be purged | Stored, pipeline not built |
| `legal_hold` | Blocks archive and purge | Enforced in archive logic |
| `archived_at` / `archived_by` | Full audit trail for archive events | Enforced |

To implement scheduled purge in Phase 2: query `purge_eligible_at <= now() AND legal_hold=False AND is_archived=True` via a Celery Beat task.

---

## Test Coverage

Test file: `apps/communications/tests/test_search_archive.py`  
**82 tests** across 13 test classes.

| Class | Coverage |
|-------|---------|
| `TestBuildSearchSnippet` | Snippet extraction, edge cases |
| `TestCheckCommunicationAccess` | Participant gate, wrong tenant, deleted thread |
| `TestGlobalSearchService` | Body match, subject match, no match, permission gate, snippet/nav, archived toggle, thread_type filter, notification search, notification user scoping |
| `TestCrossTenantIsolation` | Tenant A cannot see Tenant B data in either direction |
| `TestInternalThreadAccess` | Candidate cannot see recruiter internal thread; recruiter can |
| `TestThreadSearchService` | Text match, no match, non-participant denied, snippet+nav, pagination, sender filter |
| `TestArchiveService` | Archive, unarchive, non-participant blocked, nonexistent thread, legal hold, idempotency, search exclusion, include_archived recovery |
| `TestArchivedThreadList` | Only archived returned, metadata present |
| `TestEntityCommunicationHistory` | Linked message in timeline, linked notification in timeline, unlinked excluded, type labels, newest-first sort, non-participant excluded |
| `TestNotificationHistoryService` | All/unread/read filter, archived exclude, severity, query, pagination, other-user leakage blocked |
| `TestRecentCommunications` | Active threads only, archived excluded, limit respected, unread_count present |
| `TestSearchEndpoints` | All 18 API views — status codes, response shapes, auth enforcement |
| `TestPaginationEnforcement` | Limit respected, max cap (200), offset pages non-overlapping |

---

## Files Modified / Created

| File | Action |
|------|--------|
| `apps/communications/search_service.py` | Rewritten — complete service |
| `apps/communications/search_views.py` | Rewritten — 7 views |
| `apps/communications/urls.py` | Added 2 routes (`/messages/archived/`, `/communications/recent/`) |
| `apps/communications/migrations/0011_search_archive_indexes.py` | Created — 13 indexes |
| `apps/communications/tests/test_search_archive.py` | Created — 82 tests |
