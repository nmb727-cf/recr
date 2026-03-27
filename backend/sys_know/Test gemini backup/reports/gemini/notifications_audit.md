# Module Audit: notifications

## 1. Backend Files Found

* `apps/notifications/`: **EMPTY MODULE** (contains only `__init__.py`).
* **ACTUAL LOCATION**: The notification logic is currently residing within the `communications` module.
* `apps/communications/models.py`: Defines the `Notification` model.
* `apps/communications/views.py`: Contains `NotificationListView`, `NotificationReadView`, and `NotificationReadAllView`.
* `apps/communications/urls.py`: Maps the `/notifications/` endpoints.

## 2. Frontend Usage Found

* `../frontend/src/api/notifications.ts`: Integration for fetching the notification feed, marking individual notifications as read, and marking all as read.

## 3. Confirmed Backend Features

* **In-App Notification Feed**: Support for user-specific notifications with titles, bodies, and actionable URLs.
* **Read Status Tracking**: Individual and bulk marking of notifications as read.
* **Metadata Support**: Flexible JSON payload for storing additional notification context.
* **Soft Expiry**: Supports archiving or deleting notifications from the feed.

## 4. Confirmed Frontend Features

* **Notification Bell/Feed**: UI for displaying a list of recent alerts to the user.
* **Unread Indicators**: Visual cues for unread notifications.
* **Actionable Alerts**: Clicking a notification redirects the user to the relevant system entity (e.g., a specific candidate profile or job).

## 5. Backend Without Frontend

* **Priority Levels**: The `Notification` model supports priority/importance levels (e.g., `info`, `warning`, `critical`), which may not be fully distinguished in the current UI.

## 6. Frontend Without Backend

* None identified. The backend provides the standard set of notification management endpoints.

## 7. Validation / Error Handling Gaps

* **Missing Real-Time Support**: There is no evidence of WebSocket or Server-Sent Events (SSE) support in the current notification views; it relies on client-side polling or manual refresh.
* **Rate Limiting**: Marking all as read could be a heavy operation if a user has thousands of unread notifications; it needs a limit on the number of records updated per request.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found for notifications.
* **Priority**: Integration tests for bulk read operations and user-specific feed filtering.

## 9. Schema / API Documentation Gaps

* **Generic Success Responses**: The notification views lack `@extend_schema` decorators, resulting in generic response definitions in OpenAPI.

## 10. Security / Permission Concerns

* **Direct ID Access**: `NotificationReadView` should strictly verify that the notification being marked as read belongs to the authenticated user.
* **Actually, it does `recipient=request.user`, which is good.**

## 11. Stability / Architecture Concerns

* **Module Fragmentation**: The existence of an empty `apps/notifications` module while logic lives in `apps/communications` is confusing and should be resolved by either moving the logic or removing the empty module.
* **Database Load**: A large number of notifications per user can lead to slow feed queries if indexes on `recipient` and `created_at` are not optimized.

## 12. Priority Fixes

### High
* **Consolidate Module**: Move notification logic from `communications` to the dedicated `notifications` app to align with the intended project structure.
* **Implement Tests**: Add core tests for notification feed and read actions.

### Medium
* **Implement Real-time Alerts**: Add WebSocket support for pushing notifications to active users without polling.

### Low
* **Cleanup Empty Module**: Remove `apps/notifications` if the decision is to keep the logic in `communications`.

## 13. Unverified Items

* Push notification support (FCM/APNS) (UNVERIFIED).
* Email notification fallback logic (UNVERIFIED).

## 14. Recommended Next Tests

* `test_notification_feed_isolation`: Verify that users only see their own notifications.
* `test_mark_all_as_read_limit`: Verify that marking all as read only affects the current user's unread notifications.
* `test_notification_action_url_integrity`: Verify that action URLs are correctly persisted and returned.
* `test_unread_count_accuracy`: Verify that the unread count correctly decrements after marking a notification as read.
