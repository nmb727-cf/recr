# Phase 26: Interview Analytics Foundation

Prompt ID: `ICC-INTERVIEW-ANALYTICS-FOUNDATION-26`  
Phase: `Interview Command Center / Analytics Layer / Phase 26`  
Module: `Interview Analytics Foundation`

## Scope

Tenant-scoped foundational analytics infrastructure for Interview Command Center across execution engines, flows, scorecards, automation, and decisions.

Supports:

- interview performance analytics
- candidate performance analytics
- interviewer performance analytics
- flow efficiency analytics
- stage conversion analytics
- score distribution analytics
- automation effectiveness analytics
- SLA and scheduling analytics
- drop-off analytics
- quality analytics
- predictive analytics readiness
- AI learning input readiness

Candidate will only see limited personal analytics later. This foundation is for recruiter, ops, governance, and executive analytics use.

## 1. System Architecture

- Shared layer: `InterviewAnalyticsFoundation`
- Core components:
  - Analytics event collector
  - Metrics aggregation engine
  - Interview performance engine
  - Candidate performance engine
  - Interviewer performance engine
  - Flow efficiency engine
  - Scorecard analytics engine
  - Automation effectiveness engine
  - Scheduling & SLA analytics engine
  - Drop-off & conversion engine
  - Data warehouse / aggregation layer
  - Query & filter engine
  - Visualization data layer
  - Analytics audit & versioning layer

Architecture layers:

- event layer
- aggregation layer
- metrics layer
- query layer
- visualization layer
- audit layer

Data pipeline:

1. Execution engines, flow engine, automation layer, scorecard layer, and decision layer emit analytics events.
2. Event collector validates, deduplicates, and stores raw analytics events.
3. Aggregation engine computes real-time and batch metrics.
4. Aggregated metrics are stored by tenant, time bucket, entity, and dimension.
5. Query layer serves filtered, cached, and drill-down analytics.
6. Visualization layer powers dashboards and comparative views.
7. Analytics outputs also feed AI learning and optimization layers.

Operating model:

- real-time metrics for operational visibility
- batch / recomputed metrics for heavier analytical views
- time-series and dimensional analytics supported
- tenant isolation enforced at event, aggregate, and query layers
- company and agency analytics remain isolated by tenant and context rules

Design rules:

- metric definition versioning is mandatory
- raw event auditability is preserved
- query layer favors pre-aggregation and caching for scale
- analytics foundation is AI-learning-ready but not dependent on future modules

## 2. Database Design

Primary entities:

- `interview_analytics_event`
- `interview_analytics_metric`
- `interview_analytics_dimension`
- `interview_analytics_aggregate`
- `interview_performance_metric`
- `candidate_performance_metric`
- `interviewer_performance_metric`
- `flow_efficiency_metric`
- `scorecard_distribution_metric`
- `automation_effectiveness_metric`
- `sla_performance_metric`
- `dropoff_conversion_metric`
- `analytics_query_cache`
- `analytics_metric_definition`
- `analytics_aggregation_log`

Key fields:

- `tenant_id`
- `entity_type`
- `entity_id`
- `interview_id`
- `flow_id`
- `stage_id`
- `candidate_id`
- `interviewer_id`
- `job_id`
- `metric_name`
- `metric_value`
- `dimension_payload`
- `time_bucket`
- `aggregation_type`
- `event_type`
- `source_module`
- `created_at`
- `updated_at`

Entity purposes:

- `interview_analytics_event`: raw analytics event stream
- `interview_analytics_metric`: normalized metric facts
- `interview_analytics_dimension`: dimensional attributes and denormalized lookup values
- `interview_analytics_aggregate`: rolled-up metric aggregates
- `interview_performance_metric`: interview-specific KPIs
- `candidate_performance_metric`: candidate-level metrics
- `interviewer_performance_metric`: interviewer-level metrics
- `flow_efficiency_metric`: flow/stage timing and bottleneck metrics
- `scorecard_distribution_metric`: score spread and scoring behavior metrics
- `automation_effectiveness_metric`: automation impact metrics
- `sla_performance_metric`: deadlines, lag, and SLA breach metrics
- `dropoff_conversion_metric`: funnel and conversion metrics
- `analytics_query_cache`: cached query results
- `analytics_metric_definition`: metric versioning and computation definitions
- `analytics_aggregation_log`: aggregation and recomputation state

## 3. API Structure

**Analytics APIs**

- Fetch interview performance metrics
- Fetch candidate performance metrics
- Fetch interviewer performance metrics
- Fetch flow efficiency metrics
- Fetch score distribution metrics
- Fetch automation effectiveness metrics
- Fetch SLA analytics
- Fetch drop-off analytics
- Fetch conversion analytics

**Query APIs**

- Fetch analytics with filters
- Fetch analytics by dimension
- Fetch analytics by time range
- Fetch analytics by job / role / department
- Fetch analytics by interview type
- Fetch analytics by tenant scope
- Fetch aggregated analytics
- Fetch time-series analytics

**Aggregation APIs**

- Trigger metric aggregation
- Fetch aggregation status
- Refresh cache
- Recompute analytics if needed

Rules:

- APIs are tenant-scoped by default.
- Operational dashboards may use fresher near-real-time data.
- Historical and heavy analytics prefer cached/pre-aggregated reads.
- Metric definition version is included in responses where needed for explainability.

## 4. UI Architecture

UI includes:

- Interview analytics dashboard
- Candidate performance dashboard
- Interviewer performance dashboard
- Flow efficiency dashboard
- Score distribution dashboard
- Automation effectiveness dashboard
- SLA analytics dashboard
- Drop-off analytics dashboard
- Conversion analytics dashboard
- Filter / drill-down interface
- Time-series charts
- Heatmap views
- Comparison views

Key UI modes:

1. Executive Overview
2. Interview Performance
3. Candidate Quality
4. Interviewer Effectiveness
5. Flow Bottleneck Analysis
6. Automation Effectiveness
7. SLA / Operational Efficiency
8. Conversion & Drop-off Analysis

UI rules:

- enterprise-grade dashboard layout
- fast filtering
- multi-dimensional drill-down
- time-range comparison
- tenant-isolated views
- no heavy blocking queries in user path

## 5. Execution Flow

1. Execution engines emit analytics events.
2. Event collector stores raw analytics events.
3. Aggregation engine computes metrics.
4. Metrics are stored in analytics aggregates.
5. Query layer fetches analytics.
6. UI dashboards render analytics.
7. Caching layer optimizes performance.
8. Analytics feeds AI learning layer.

Supported metric families:

- Interview metrics:
  - interviews scheduled
  - interviews completed
  - no-show rate
  - completion rate
  - average interview duration
- Candidate metrics:
  - pass rate
  - fail rate
  - average score
  - stage progression rate
- Interviewer metrics:
  - scoring variance
  - average candidate score
  - feedback turnaround time
- Flow metrics:
  - stage conversion rate
  - bottleneck detection
  - average stage time
- Automation metrics:
  - reminders sent
  - escalations triggered
  - automation success rate
- SLA metrics:
  - deadline breaches
  - response time
- Conversion metrics:
  - candidate drop-off
  - offer conversion

## 6. Edge Cases

- Delayed analytics events
- Duplicate analytics events
- Missing dimension data
- Tenant migration
- Metric definition changes
- Recomputation requirements
- Large dataset performance

Handling rules:

- Duplicate events are deduped using event identity and correlation controls.
- Metric definition changes trigger versioned recomputation paths.
- Missing dimensions degrade gracefully with explicit unknown buckets where appropriate.
- Large datasets rely on partitioning, pre-aggregation, and cache-first dashboard access.

## 7. Enterprise Features

- Tenant-scoped analytics foundation
- Real-time and aggregated metric support
- Time-series and dimensional analytics model
- Metric definition versioning
- Large-scale aggregation and cache strategy
- Flow, scorecard, automation, and SLA analytics support
- Auditability of raw events and computed metrics
- AI learning input readiness
- Reusable analytics base for advanced predictive layers

## 8. Integration Mapping

- `All Execution Engines`
- `Flow Engine`
- `Automation Layer`
- `Scorecard Engine`
- `Decision Engine`
- `AI Builder Learning Layer`
- `Governance / Audit Layer`

