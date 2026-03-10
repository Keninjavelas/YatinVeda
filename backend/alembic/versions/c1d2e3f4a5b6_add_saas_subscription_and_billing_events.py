"""add_saas_subscription_and_billing_events

Revision ID: c1d2e3f4a5b6
Revises: b8c9d7e2f1a3
Create Date: 2026-03-08 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b8c9d7e2f1a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = set(inspector.get_table_names())

    def index_exists(table: str, name: str) -> bool:
        if table not in tables:
            return False
        indexes = inspector.get_indexes(table)
        return any(idx.get("name") == name for idx in indexes)

    if "user_subscriptions" not in tables:
        op.create_table(
            "user_subscriptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("subscription_plan", sa.String(length=30), nullable=False, server_default="starter"),
            sa.Column("subscription_status", sa.String(length=30), nullable=False, server_default="trial"),
            sa.Column("trial_ends_at", sa.DateTime(), nullable=True),
            sa.Column("plan_expires_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        tables.add("user_subscriptions")

    if not index_exists("user_subscriptions", "ix_user_subscriptions_id"):
        op.create_index("ix_user_subscriptions_id", "user_subscriptions", ["id"], unique=False)
    if not index_exists("user_subscriptions", "ix_user_subscriptions_user_id"):
        op.create_index("ix_user_subscriptions_user_id", "user_subscriptions", ["user_id"], unique=False)

    if "subscription_audit_logs" not in tables:
        op.create_table(
            "subscription_audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=False),
            sa.Column("target_user_id", sa.Integer(), nullable=False),
            sa.Column("old_plan", sa.String(length=30), nullable=True),
            sa.Column("new_plan", sa.String(length=30), nullable=False),
            sa.Column("old_status", sa.String(length=30), nullable=True),
            sa.Column("new_status", sa.String(length=30), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("subscription_audit_logs")

    if not index_exists("subscription_audit_logs", "ix_subscription_audit_logs_id"):
        op.create_index("ix_subscription_audit_logs_id", "subscription_audit_logs", ["id"], unique=False)
    if not index_exists("subscription_audit_logs", "ix_subscription_audit_logs_actor_user_id"):
        op.create_index("ix_subscription_audit_logs_actor_user_id", "subscription_audit_logs", ["actor_user_id"], unique=False)
    if not index_exists("subscription_audit_logs", "ix_subscription_audit_logs_target_user_id"):
        op.create_index("ix_subscription_audit_logs_target_user_id", "subscription_audit_logs", ["target_user_id"], unique=False)
    if not index_exists("subscription_audit_logs", "ix_subscription_audit_logs_created_at"):
        op.create_index("ix_subscription_audit_logs_created_at", "subscription_audit_logs", ["created_at"], unique=False)

    if "billing_webhook_events" not in tables:
        op.create_table(
            "billing_webhook_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=40), nullable=False),
            sa.Column("event_id", sa.String(length=120), nullable=True),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("idempotency_key", sa.String(length=200), nullable=False),
            sa.Column("signature", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="received"),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("received_at", sa.DateTime(), nullable=False),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idempotency_key"),
        )
        tables.add("billing_webhook_events")

    if not index_exists("billing_webhook_events", "ix_billing_webhook_events_id"):
        op.create_index("ix_billing_webhook_events_id", "billing_webhook_events", ["id"], unique=False)
    if not index_exists("billing_webhook_events", "ix_billing_webhook_events_provider"):
        op.create_index("ix_billing_webhook_events_provider", "billing_webhook_events", ["provider"], unique=False)
    if not index_exists("billing_webhook_events", "ix_billing_webhook_events_event_id"):
        op.create_index("ix_billing_webhook_events_event_id", "billing_webhook_events", ["event_id"], unique=False)
    if not index_exists("billing_webhook_events", "ix_billing_webhook_events_event_type"):
        op.create_index("ix_billing_webhook_events_event_type", "billing_webhook_events", ["event_type"], unique=False)
    if not index_exists("billing_webhook_events", "ix_billing_webhook_events_idempotency_key"):
        op.create_index("ix_billing_webhook_events_idempotency_key", "billing_webhook_events", ["idempotency_key"], unique=True)
    if not index_exists("billing_webhook_events", "ix_billing_webhook_events_status"):
        op.create_index("ix_billing_webhook_events_status", "billing_webhook_events", ["status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "billing_webhook_events" in tables:
        op.drop_table("billing_webhook_events")

    if "subscription_audit_logs" in tables:
        op.drop_table("subscription_audit_logs")

    if "user_subscriptions" in tables:
        op.drop_table("user_subscriptions")
