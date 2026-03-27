# Module Audit: analytics

## 1. Backend Files Found

* `apps/analytics/views.py`: Contains high-level dashboard and domain-specific analytics views (Recruitment, Pipeline, Agency, Candidate, Interview).
* `apps/analytics/urls.py`: Unified URL patterns for all analytics endpoints.

## 2. Frontend Usage Found

* `../frontend/src/api/analytics.ts`: Comprehensive integration for fetching dashboard metrics and detailed recruitment reports.
* The frontend uses all available analytics endpoints for its reporting suite.

## 3. Confirmed Backend Features

* **Platform Dashboard**: Aggregated metrics for jobs, candidates, and applications for the current tenant.
* **Hiring Funnel Engine**: Calculation of shortlist, offer, and join rates based on application status transitions.
* **Pipeline Stale Tracking**: Identification of applications that have remained in the same stage for more than 7 days.
* **Agency Performance Benchmarking**: Breakdown of submission-to-hire rates for agency partners.
* **Source Attribution**: Analyzing candidate volume and quality by sourcing channel.
* **Interview Quality Monitoring**: Tracking interview status and average scores across different interview types.

## 4. Confirmed Frontend Features

* **Analytics Reporting Suite**: Dedicated interface for recruiters and hiring managers to visualize funnel performance and pipeline health.
* **Dashboard Summary**: Real-time (refresh-based) overview of tenant activity on the landing page.

## 5. Backend Without Frontend

* **Time-range Filtering**: The backend views (e.g., `RecruitmentAnalyticsView`) support `start_date` and `end_date` parameters, which may not be fully exposed in all UI dashboard components.

## 6. Frontend Without Backend

* None identified. The backend provides a solid data aggregation layer for all current frontend analytics needs.

## 7. Validation / Error Handling Gaps

* **Incomplete Filtering**: `RecruitmentAnalyticsView` retrieves `department_id` from the query string but fails to apply it to the application queryset, making department-specific reporting non-functional.
* **Calculated Field Risks**: Funnel rates (e.g., `join_rate`) are calculated in-memory in the view; for very large datasets, these should be moved to database-level annotations for performance.
* **Missing Null Handling**: `InterviewAnalyticsView` returns the raw result of the `Avg` aggregate, which may be `null` for new tenants, potentially causing UI rendering issues if not handled.

## 8. Testing Coverage Gaps

* **CRITICAL**: No tests found in `backend/apps/analytics/`. Analytical logic is prone to regressions when model statuses or business rules change.
* **Priority**: Integration tests for funnel rate calculations and stale application identification.

## 9. Schema / API Documentation Gaps

* **Generic Success Responses**: All analytics views lack `@extend_schema` decorators, resulting in generic `any` or `record` types in the OpenAPI documentation.
* **Undocumented Query Parameters**: Parameters like `department_id`, `start_date`, and `end_date` are not explicitly defined in the API schema.

## 10. Security / Permission Concerns

* **Insufficient RBAC**: Analytics endpoints currently only require `IsAuthenticated`. Access to sensitive hiring performance data and agency benchmarking should be restricted to `HR_MANAGER` or `TENANT_ADMIN` roles.
* **Tenant Isolation**: Query filtering correctly uses `request.user.tenant_id` to ensure data privacy between clients.

## 11. Stability / Architecture Concerns

* **Performance Bottlenecks**: As the number of applications and candidates grows, performing `count()` and `Avg()` aggregates on every request will slow down the dashboard. These should eventually be cached or moved to a pre-aggregated analytics table.
* **Logic Duplication**: Much of the status-based counting logic is repeated across different views within `views.py`.

## 12. Priority Fixes

### High
* **Fix Department Filter**: Implement the missing `department_id` filter in `RecruitmentAnalyticsView`.
* **Implement Role-based Access**: Restrict analytics access to authorized managerial roles.
* **Implement Tests**: Add a test suite to verify the accuracy of funnel calculations and stale tracking.

### Medium
* **Enhance OpenAPI Documentation**: Add detailed schemas for all analytics response payloads.
* **Implement Caching**: Add a short-term cache (e.g., 1 hour) for heavy dashboard metrics.

### Low
* **Centralize Aggregation Logic**: Move common counting and status-grouping logic to a shared service or utility class.

## 13. Unverified Items

* Support for custom dashboard widgets (UNVERIFIED).
* Exporting analytics data to CSV/Excel (UNVERIFIED).

## 14. Recommended Next Tests

* `test_funnel_rate_calculation`: Verify that the shortlist and join rates are calculated correctly from application statuses.
* `test_stale_application_threshold`: Verify that applications updated more than 7 days ago are correctly identified as stale.
* `test_tenant_data_leak_prevention`: Verify that analytics for Tenant A do not include any data from Tenant B.
* `test_date_range_filtering`: Verify that providing `start_date` and `end_date` correctly restricts the recruitment metrics.
* `test_interview_avg_score_with_no_data`: Verify that the system handles tenants with no completed interviews gracefully.
