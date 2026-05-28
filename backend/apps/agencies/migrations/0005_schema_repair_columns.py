from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('agencies', '0004_emailtrackingconfig_guestportal_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- agencies_client_relationship parity
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS allocated_team_id uuid NULL;
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS allocated_user_id uuid NULL;
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS auto_accept_jobs boolean NOT NULL DEFAULT false;
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS client_name varchar(255) NULL;
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS contract_snapshot jsonb NULL;
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS email_domain varchar(255) NOT NULL DEFAULT '';
            ALTER TABLE agencies_client_relationship ADD COLUMN IF NOT EXISTS refund_type varchar(50) NOT NULL DEFAULT '';

            -- agencies_job_assignment parity
            ALTER TABLE agencies_job_assignment ADD COLUMN IF NOT EXISTS acceptance_mode varchar(20) NOT NULL DEFAULT 'manual';
            ALTER TABLE agencies_job_assignment ADD COLUMN IF NOT EXISTS accepted_at timestamptz NULL;
            ALTER TABLE agencies_job_assignment ADD COLUMN IF NOT EXISTS accepted_by_id uuid NULL;
            ALTER TABLE agencies_job_assignment ADD COLUMN IF NOT EXISTS assigned_team_id uuid NULL;

            -- agencies_email_tracking parity
            ALTER TABLE agencies_email_tracking ADD COLUMN IF NOT EXISTS tenant_id uuid NULL;
            ALTER TABLE agencies_email_tracking ADD COLUMN IF NOT EXISTS tracking_email varchar(254) NULL;
            ALTER TABLE agencies_email_tracking ADD COLUMN IF NOT EXISTS forward_to_email varchar(254) NULL;
            ALTER TABLE agencies_email_tracking ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

            UPDATE agencies_email_tracking
            SET tracking_email = contact_email
            WHERE tracking_email IS NULL;

            -- model table missing in some DBs
            CREATE TABLE IF NOT EXISTS agencies_billing_transaction (
                id uuid PRIMARY KEY,
                tenant_id uuid NOT NULL,
                relationship_id uuid NOT NULL,
                application_id uuid NOT NULL,
                amount numeric(15,2) NOT NULL,
                currency varchar(5) NOT NULL DEFAULT 'INR',
                transaction_type varchar(50) NOT NULL,
                status varchar(50) NOT NULL DEFAULT 'pending',
                due_date date NULL,
                paid_at timestamptz NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                metadata jsonb NOT NULL DEFAULT '{}'::jsonb
            );

            CREATE INDEX IF NOT EXISTS agencies_billing_transaction_tenant_id_idx
            ON agencies_billing_transaction(tenant_id);
            CREATE INDEX IF NOT EXISTS agencies_billing_transaction_application_id_idx
            ON agencies_billing_transaction(application_id);
            CREATE INDEX IF NOT EXISTS agencies_billing_transaction_relationship_id_idx
            ON agencies_billing_transaction(relationship_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS agencies_billing_transaction_relationship_id_idx;
            DROP INDEX IF EXISTS agencies_billing_transaction_application_id_idx;
            DROP INDEX IF EXISTS agencies_billing_transaction_tenant_id_idx;
            DROP TABLE IF EXISTS agencies_billing_transaction;

            ALTER TABLE agencies_email_tracking DROP COLUMN IF EXISTS is_active;
            ALTER TABLE agencies_email_tracking DROP COLUMN IF EXISTS forward_to_email;
            ALTER TABLE agencies_email_tracking DROP COLUMN IF EXISTS tracking_email;
            ALTER TABLE agencies_email_tracking DROP COLUMN IF EXISTS tenant_id;

            ALTER TABLE agencies_job_assignment DROP COLUMN IF EXISTS assigned_team_id;
            ALTER TABLE agencies_job_assignment DROP COLUMN IF EXISTS accepted_by_id;
            ALTER TABLE agencies_job_assignment DROP COLUMN IF EXISTS accepted_at;
            ALTER TABLE agencies_job_assignment DROP COLUMN IF EXISTS acceptance_mode;

            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS refund_type;
            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS email_domain;
            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS contract_snapshot;
            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS client_name;
            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS auto_accept_jobs;
            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS allocated_user_id;
            ALTER TABLE agencies_client_relationship DROP COLUMN IF EXISTS allocated_team_id;
            """,
        ),
    ]
