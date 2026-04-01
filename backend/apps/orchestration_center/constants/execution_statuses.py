from django.db import models


class ProviderStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    DEGRADED = 'degraded', 'Degraded'
    DISABLED = 'disabled', 'Disabled'
    DEPRECATED = 'deprecated', 'Deprecated'


class HealthStatus(models.TextChoices):
    UNKNOWN = 'unknown', 'Unknown'
    HEALTHY = 'healthy', 'Healthy'
    WARNING = 'warning', 'Warning'
    UNHEALTHY = 'unhealthy', 'Unhealthy'


class PromptStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    ACTIVE = 'active', 'Active'
    REJECTED = 'rejected', 'Rejected'
    ARCHIVED = 'archived', 'Archived'


class ApprovalMode(models.TextChoices):
    SUGGESTION_ONLY = 'suggestion_only', 'Suggestion Only'
    AUTO_APPLY = 'auto_apply', 'Auto Apply'
    APPROVAL_REQUIRED = 'approval_required', 'Approval Required'


class AIExecutionStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    PARTIAL = 'partial', 'Partial'
    REQUIRES_REVIEW = 'requires_review', 'Requires Review'
    CANCELLED = 'cancelled', 'Cancelled'


class ValidationStatus(models.TextChoices):
    NOT_CHECKED = 'not_checked', 'Not Checked'
    VALID = 'valid', 'Valid'
    INVALID = 'invalid', 'Invalid'
    PARTIAL = 'partial', 'Partial'
    PASSED = 'passed', 'Passed'
    FAILED = 'failed', 'Failed'


class ReviewStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    RETURNED = 'returned', 'Returned'
    NOT_REQUIRED = 'not_required', 'Not Required'


class ApplicationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPLIED = 'applied', 'Applied'
    NOT_APPLIED = 'not_applied', 'Not Applied'


class AutomationRuleStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    PAUSED = 'paused', 'Paused'
    ARCHIVED = 'archived', 'Archived'
    TESTING = 'testing', 'Testing'


class AutomationExecutionStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    SCHEDULED = 'scheduled', 'Scheduled'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    PARTIAL = 'partial', 'Partial'
    CANCELLED = 'cancelled', 'Cancelled'
    REQUIRES_REVIEW = 'requires_review', 'Requires Review'


class ScheduledActionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    DISPATCHED = 'dispatched', 'Dispatched'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED = 'failed', 'Failed'


class FailureStatus(models.TextChoices):
    NEW = 'new', 'New'
    TRIAGED = 'triaged', 'Triaged'
    RETRYING = 'retrying', 'Retrying'
    RESOLVED = 'resolved', 'Resolved'
    MOVED_TO_DEAD_LETTER = 'moved_to_dead_letter', 'Moved to Dead Letter'
    IGNORED = 'ignored', 'Ignored'


class FailureSeverity(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class ApprovalStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    EXPIRED = 'expired', 'Expired'
    CANCELLED = 'cancelled', 'Cancelled'


class SuggestionCategory(models.TextChoices):
    FOLLOWUP_RECOMMENDATION = 'followup_recommendation', 'Follow-up Recommendation'
    ESCALATION_RECOMMENDATION = 'escalation_recommendation', 'Escalation Recommendation'
    REVIEW_RECOMMENDATION = 'review_recommendation', 'Review Recommendation'
    ASSIGNMENT_RECOMMENDATION = 'assignment_recommendation', 'Assignment Recommendation'
    COMMUNICATION_DRAFT = 'communication_draft', 'Communication Draft'
    RISK_FLAG_RECOMMENDATION = 'risk_flag_recommendation', 'Risk Flag Recommendation'
    DEADLINE_RECOMMENDATION = 'deadline_recommendation', 'Deadline Recommendation'
    INSIGHT_SUMMARY = 'insight_summary', 'Insight Summary'


class SuggestionStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    CONVERTED = 'converted', 'Converted'
    EXPIRED = 'expired', 'Expired'
    SUPERSEDED = 'superseded', 'Superseded'
    FAILED = 'failed', 'Failed'


class SuggestionConversionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONVERTED = 'converted', 'Converted'
    FAILED = 'failed', 'Failed'


class ConfidenceBand(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'


class ConnectorStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    DISABLED = 'disabled', 'Disabled'
    TESTING = 'testing', 'Testing'


class DeadLetterStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    REQUEUED = 'requeued', 'Requeued'
    RESOLVED = 'resolved', 'Resolved'
    IGNORED = 'ignored', 'Ignored'
