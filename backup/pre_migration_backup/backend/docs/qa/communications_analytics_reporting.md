# Communication Analytics and Reporting

**Prompt ID:** COMMS-ANALYTICS-AND-REPORTING-01  
**Module:** Communications Engine — Analytics & Reporting Layer  
**Status:** Complete (Phase 1)

---

## Overview

The Communication Analytics and Reporting layer provides pre-aggregated operational intelligence across all communication activity on the platform. It surfaces messaging volume, channel delivery health, notification effectiveness, response-time performance, fallback/escalation patterns, entity-level coordination load, and team workload visibility.

This is the reporting intelligence layer for the communication engine. Every metric is derived from real event data — no synthetic or disconnected analytics.

Any authenticated user can access analytics scoped to their tenant. No cross-tenant data is ever reachable. No message content is exposed in any analytics payload. All responses are shaped for dashboard and chart rendering.

---

## Architecture

### Data Sources

| Source Model | What It Drives |
|-------------|---------------|
| `MessageThread` | Thread counts, active/archived splits, entity grouping |
| `Message` | Volume, sender workload, entity-linked message counts, response-time CTE |
| `ThreadParticipant` | Thread participation per user |
| `Notification` | Effectiveness (read/expiry/fallback rates), notification volume, backlog |
| `NotificationDelivery` | In-app and email channel delivery stats |
| `CommunicationDelivery` | WhatsApp, SMS, push channel delivery stats |
| `NotificationAutomationJob` | Fallback job analytics (scheduled / executed / cancelled) |
| `NotificationEscalationLog` | Escalation counts, resolution rates |

### Query Strategy (Phase 1)

PostgreSQL aggregations and `GROUP BY` queries via Django ORM. One CTE via raw SQL for `PERCENTILE_CONT` (response time percentiles — not available in Django ORM).

Future path: ClickHouse or analytics warehouse can be plugged in by replacing the service layer implementations — the view layer is fully abstracted from the query backend.

### Tenant Isolation

Every service method accepts `tenant_id` as its first argument. It is applied as the leading filter on every query before any aggregation runs. Cross-tenant data access is architecturally impossible.

---

## Metric Definitions

| Metric | Definition |
|--------|-----------|
| `first_response_time` | Seconds between the first message in a thread and the first reply from a **different** participant. Capped at 7 days to exclude outliers. |
| `notification_read_rate` | `read_count / total_created` within the queried window. |
| `fallback_trigger_rate` | Notifications that had a fallback email or WhatsApp sent / total notifications created. |
| `fallback_cancel_rate` | Fallback automation jobs cancelled (notification read before job fired) / fallback jobs scheduled. **High = healthy** (user responded before needing fallback). |
| `escalation_resolution_rate` | Escalation log entries where the original notification was later read / total escalation log entries. |
| `unread_backlog` | Active, unread, non-expired notification count per user. |

---

## Key Components

### Service: `CommunicationAnalyticsService`

Located at `apps/communications/analytics_service.py`.

All methods are `@staticmethod`. All return plain `dict` objects shaped for dashboard/chart use.

#### `get_communication_dashboard_metrics(...)`

```python
get_communication_dashboard_metrics(
    *,
    tenant_id,
    date_from=None,   # datetime
    date_to=None,     # datetime
) -> Dict
```

Returns:
```json
{
  "period": {"date_from": "...", "date_to": "..."},
  "messaging": {
    "total_messages": 1234,
    "total_threads": 89,
    "active_threads": 65,
    "archived_threads": 24,
    "internal_threads": 55,
    "external_threads": 34,
    "messages_by_type": [{"message_type": "text", "count": 900}, ...],
    "messages_by_entity": [{"related_entity_type": "candidate", "count": 400}, ...],
    "threads_by_type": [{"thread_type": "interview_coordination", "count": 30}, ...]
  },
  "notifications": {
    "total_notifications": 567,
    "read_notifications": 445,
    "unread_active": 34,
    "fallback_emails_sent": 12,
    "fallback_whatsapp_sent": 5,
    "escalations_triggered": 3,
    "notifications_escalated": 8,
    "by_category": [{"type": "interview", "count": 120}, ...],
    "by_severity": [{"severity": "info", "count": 400}, ...]
  },
  "delivery": {
    "total_failed_deliveries": 8,
    "notification_delivery_failed": 3,
    "channel_delivery_failed": 5,
    "notification_channel_summary": [...],
    "multi_channel_summary": [...]
  }
}
```

#### `get_channel_performance_report(...)`

```python
get_channel_performance_report(
    *,
    tenant_id,
    date_from=None,
    date_to=None,
    channel_type: str = "",   # filter to one channel
) -> Dict
```

Merges `NotificationDelivery` (in_app, email) and `CommunicationDelivery` (whatsapp, sms, push) into a unified per-channel breakdown.

Returns:
```json
{
  "channels": [
    {
      "channel": "email",
      "total_attempts": 234,
      "delivered": 210,
      "sent": 10,
      "failed": 14,
      "pending": 0,
      "skipped": 0,
      "success_rate": 0.9402,
      "failure_rate": 0.0598
    }
  ],
  "best_channel": "in_app",
  "worst_channel": "sms",
  "total_attempts": 890,
  "total_failed": 22
}
```

`success_rate` = (delivered + sent) / total_attempts.

#### `get_notification_effectiveness_report(...)`

```python
get_notification_effectiveness_report(
    *,
    tenant_id,
    date_from=None,
    date_to=None,
    category: str = "",   # filter by notification type
    priority: str = "",   # filter by severity
) -> Dict
```

Returns overall `totals` dict plus `by_severity` and `by_category` breakdowns. Each breakdown row includes `count`, `read_count`, and `read_rate`.

#### `get_response_time_report(...)`

```python
get_response_time_report(
    *,
    tenant_id,
    date_from=None,
    date_to=None,
    thread_type: str = "",
    user_id=None,    # narrow to threads started by this sender
) -> Dict
```

Returns `messaging_response_times` (avg, p50, p90 in seconds + human-readable strings) and `notification_read_latency` (avg seconds + by_severity breakdown).

The p50/p90 values are computed using PostgreSQL `PERCENTILE_CONT` via a raw SQL CTE. Response times > 7 days are excluded as outliers.

#### `get_fallback_escalation_report(...)`

```python
get_fallback_escalation_report(
    *,
    tenant_id,
    date_from=None,
    date_to=None,
) -> Dict
```

Returns `fallbacks` dict (job counts, cancel_rate, execution_rate, by_job_type, noisy_triggers) and `escalations` dict (counts, send_rate, resolution_rate, by_level).

`noisy_triggers`: top 10 `event_key` values with the most executed fallback jobs — candidates for rule timing tuning.

#### `get_entity_communication_report(...)`

```python
get_entity_communication_report(
    *,
    tenant_id,
    entity_type: str = "",    # candidate, job, application, interview, offer, agency
    entity_id=None,            # UUID — if set, returns single-entity detail
    date_from=None,
    date_to=None,
    limit: int = 20,           # max 100
    offset: int = 0,
) -> Dict
```

**Single entity mode** (entity_id provided): Returns full detail — thread_count, active_threads, archived_threads, message_count, notification_count, threads_by_type, messages_by_type.

**List mode** (entity_id omitted): Returns ranked list of most active entities with thread_count, message_count, notification_count per entity. Paginated.

#### `get_workload_report(...)`

```python
get_workload_report(
    *,
    tenant_id,
    date_from=None,
    date_to=None,
    user_id=None,    # single-user summary if provided
    limit: int = 20, # max 50
    offset: int = 0,
) -> Dict
```

**Tenant-wide mode**: Returns `top_senders`, `highest_unread_backlog`, `highest_thread_participation` ranked lists. Only `user_id` UUIDs and counts are exposed — no message content.

**Single-user mode** (user_id provided): Returns `messages_sent`, `threads_participated`, `unread_backlog`, `internal_messages_sent`, `external_messages_sent`.

---

### Module-level helpers

```python
_safe_rate(numerator: int, denominator: int) -> Optional[float]
    # Returns numerator/denominator rounded to 4dp, or None when denom=0.

_seconds_to_human(seconds) -> Optional[str]
    # Converts a float second count to "1h 23m", "45s", "2d 3h", etc.

_apply_date_filter(qs, field: str, date_from, date_to) -> QuerySet
    # Applies __gte / __lte filters when date args are not None.
```

---

### Migration: `0012_analytics_indexes`

13 composite indexes added across 4 tables.

**Message indexes:**
- `(tenant_id, message_type, sent_at)` — messages_by_type with date range
- `(tenant_id, related_entity_type, related_entity_id, sent_at)` — entity analytics
- `(tenant_id, sender_id, is_deleted, sent_at)` — sender workload

**MessageThread indexes:**
- `(tenant_id, is_deleted, is_archived, created_at)` — thread counts over time
- `(tenant_id, thread_type, is_deleted, created_at)` — thread type breakdown

**Notification indexes:**
- `(tenant_id, type, created_at)` — category breakdown
- `(tenant_id, severity, is_read, created_at)` — effectiveness by severity
- `(tenant_id, fallback_email_sent_at)` — fallback email tracking
- `(tenant_id, escalation_level, created_at)` — escalation level tracking
- `(tenant_id, is_read, created_at, read_at)` — read latency queries

**NotificationDelivery indexes:**
- `(tenant_id, channel, status, attempted_at)` — channel performance

**NotificationEscalationLog indexes:**
- `(tenant_id, status, triggered_at)` — escalation counts over time

---

## API Endpoints

All endpoints require authentication. Responses follow the project envelope: `{success, data, message}`. All queries are tenant-scoped from `request.user.tenant_id`.

### Dashboard
```
GET /api/v1/communication-analytics/dashboard/
```
Query params: `date_from`, `date_to`

### Channel Performance
```
GET /api/v1/communication-analytics/channels/
```
Query params: `date_from`, `date_to`, `channel_type`

### Notification Effectiveness
```
GET /api/v1/communication-analytics/notifications/
```
Query params: `date_from`, `date_to`, `category`, `priority`

### Response Times
```
GET /api/v1/communication-analytics/response-times/
```
Query params: `date_from`, `date_to`, `thread_type`, `user_id`

### Team / User Workload
```
GET /api/v1/communication-analytics/workload/
```
Query params: `date_from`, `date_to`, `user_id`, `limit` (max 50), `offset`

### Fallback / Escalation
```
GET /api/v1/communication-analytics/fallbacks/
```
Query params: `date_from`, `date_to`

### Entity Communication
```
GET /api/v1/communication-analytics/entities/
```
Query params: `entity_type` (candidate, job, application, interview, offer, agency), `entity_id`, `date_from`, `date_to`, `limit` (max 100), `offset`

Returns 400 if `entity_type` is not a known value, or if `entity_id` is given without `entity_type`.

---

## Business Rules

| Rule | Behaviour |
|------|-----------|
| Tenant isolation | Every query gates on `tenant_id` first. Zero cross-tenant leakage is architecturally enforced. |
| Content safety | No message body, notification body, or thread subject is returned in any analytics payload. Only UUIDs and counts. |
| Candidate access | Candidate users receive the same tenant-scoped data — no special restriction at analytics layer. Operational thread content is never exposed. |
| Empty datasets | All methods return safe zero values / empty lists when no data exists. Division by zero is guarded by `_safe_rate()`. |
| Outlier exclusion | Response times > 7 days (604,800 seconds) are excluded from averages and percentiles. |
| Pagination | Entity report (max 100) and workload report (max 50) are paginated. All other reports are bounded by date range. |
| Rate rounding | All rates are rounded to 4 decimal places. |
| Fallback cancel rate semantics | A **high** cancel_rate is healthy — it means users read the notification before the fallback needed to fire. |

---

## Frontend Contract

| UI Screen | Endpoint | Key Fields |
|-----------|---------|-----------|
| Communication health dashboard | `GET /dashboard/` | messaging.*, notifications.*, delivery.* |
| Channel comparison table | `GET /channels/` | channels[].success_rate, failure_rate, total_attempts |
| Notification read-rate chart | `GET /notifications/` | totals.read_rate, by_severity, by_category |
| Response time chart | `GET /response-times/` | avg/p50/p90 seconds + human strings |
| Team workload table | `GET /workload/` | top_senders, highest_unread_backlog |
| Fallback health panel | `GET /fallbacks/` | cancel_rate, noisy_triggers, escalations |
| Entity coordination view | `GET /entities/?entity_type=candidate` | entities[].thread_count, message_count |
| Single candidate comms drill-down | `GET /entities/?entity_type=candidate&entity_id=uuid` | detail.* |

All date/time values are ISO-8601. All rates are 0.0–1.0 floats. Human-readable strings (`avg_first_response_human`) are provided alongside raw seconds for display.

---

## Performance Notes

- All date-bounded queries use indexes with `tenant_id` as the leading column.
- The response-time CTE is the only raw SQL — all other queries use the ORM.
- `get_entity_communication_report` in list mode loads entity thread data in one aggregation query, then enriches with message and notification counts in two follow-up queries scoped to the paged entity_ids.
- Dashboard metrics perform approximately 8–10 targeted aggregation queries, each bounded by tenant_id and date range.
- Workload report uses `DISTINCT` thread count for participation — uses `thread_id, distinct=True` annotate to avoid double-counting.

---

## Test Coverage

Test file: `apps/communications/tests/test_communication_analytics.py`  
**63 tests** across 9 test classes.

| Class | Coverage |
|-------|---------|
| `TestDashboardMetrics` | Message/thread/notification counts, failed delivery count, cross-tenant isolation, date range filter, messages_by_type |
| `TestChannelPerformance` | Success rate calculation, channel filter, best_channel identification, tenant isolation, multi-channel merge, empty safety |
| `TestNotificationEffectiveness` | Read rate, fallback trigger rate, by_severity/category breakdown, category filter, priority filter, tenant isolation |
| `TestResponseTimeReport` | Read latency calculation, empty threads, tenant isolation, by_severity latency, response shape |
| `TestFallbackEscalationReport` | Job counts, cancel_rate calculation, escalation counts, resolution_rate, noisy_triggers, tenant isolation |
| `TestEntityCommunicationReport` | Single-entity thread count, message count, aggregate list mode, entity_type filter, tenant isolation, pagination limit |
| `TestWorkloadReport` | Top senders ranked, unread backlog counted, single-user summary, tenant isolation, limit respected |
| `TestAnalyticsEndpoints` | All 7 endpoints 200, 2 endpoints 401 unauthenticated, invalid entity_type 400, entity_id without type 400, dashboard key shape |
| `TestEdgeCases` | `_safe_rate` zero-denominator, normal rate, `_seconds_to_human` None/overnight, empty tenant no crash |
| `TestAnalyticsAccessControl` | Dashboard tenant B sees tenant A data as zero, workload isolation, entity report isolation, workload unauthenticated denied |

---

## Files Created / Modified

| File | Action |
|------|--------|
| `apps/communications/analytics_service.py` | Created — full service, 7 report methods |
| `apps/communications/analytics_views.py` | Created — 7 views |
| `apps/communications/urls.py` | Modified — 7 analytics routes added |
| `apps/communications/migrations/0012_analytics_indexes.py` | Created — 13 indexes |
| `apps/communications/tests/test_communication_analytics.py` | Created — 63 tests |
