from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('organisations', '0005_organisation_primary_currency_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE organisations_department
            ADD COLUMN IF NOT EXISTS parent_id uuid NULL;

            UPDATE organisations_department
            SET parent_id = parent_department_id
            WHERE parent_id IS NULL
              AND parent_department_id IS NOT NULL;

            CREATE INDEX IF NOT EXISTS organisations_department_parent_id_idx
            ON organisations_department(parent_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS organisations_department_parent_id_idx;
            ALTER TABLE organisations_department
            DROP COLUMN IF EXISTS parent_id;
            """,
        ),
    ]
