from django.db import migrations


DEDUPLICATION_SQL = """
WITH ranked_general_engagements AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY tenant_id, candidate_id
            ORDER BY
                COALESCE(last_activity_at, updated_at, started_at, created_at) DESC,
                updated_at DESC,
                started_at DESC,
                created_at DESC,
                id DESC
        ) AS row_number
    FROM candidate_engagements
    WHERE is_active = TRUE
      AND is_deleted = FALSE
      AND job_id IS NULL
),
duplicate_general_engagements AS (
    SELECT id
    FROM ranked_general_engagements
    WHERE row_number > 1
)
UPDATE candidate_engagements
SET
    is_active = FALSE,
    closed_at = COALESCE(closed_at, CURRENT_TIMESTAMP),
    closure_reason = CASE
        WHEN closure_reason IS NULL OR closure_reason = ''
            THEN 'deduplicated_duplicate_general_engagement'
        ELSE closure_reason
    END,
    last_activity_at = COALESCE(last_activity_at, CURRENT_TIMESTAMP),
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (SELECT id FROM duplicate_general_engagements);
"""


def cleanup_duplicate_active_general_engagements(apps, schema_editor):
    schema_editor.execute(DEDUPLICATION_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0012_alter_candidate_engagement_stage_and_more'),
    ]

    operations = [
        migrations.RunPython(
            cleanup_duplicate_active_general_engagements,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
