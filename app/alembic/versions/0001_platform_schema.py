"""Initial reusable platform schema.

Revision ID: 0001_platform
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_platform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_title", sa.String(), nullable=False),
        sa.Column("pricing", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("status", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_title"),
    )
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("module_name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("status", sa.Boolean(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("credits_required", sa.Numeric(10, 2), server_default="1.00", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "plan_details",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("module_limit", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id", "module_id", name="uq_plan_module"),
    )
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("auto_sub", sa.Boolean(), nullable=True),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("total_general_credits", sa.Integer(), nullable=True),
        sa.Column("general_credits_used", sa.Integer(), nullable=True),
        sa.Column("general_credits_left", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(op.f("ix_users_user_id"), "users", ["user_id"], unique=False)
    op.create_table(
        "user_subscription",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("plan_title", sa.String(), nullable=True),
        sa.Column("purchase_at", sa.DateTime(), nullable=True),
        sa.Column("purchased_id", sa.String(), nullable=True),
        sa.Column("payment_status", sa.String(), nullable=True),
        sa.Column("amount_paid", sa.Numeric(10, 2), nullable=False),
        sa.Column("expiry_at", sa.DateTime(), nullable=False),
        sa.Column("total_credits", sa.Integer(), nullable=True),
        sa.Column("credits_used", sa.Integer(), nullable=True),
        sa.Column("credits_left", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchased_id"),
    )
    op.create_index(op.f("ix_user_subscription_user_id"), "user_subscription", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_subscription_user_id"), table_name="user_subscription")
    op.drop_table("user_subscription")
    op.drop_index(op.f("ix_users_user_id"), table_name="users")
    op.drop_table("users")
    op.drop_table("plan_details")
    op.drop_table("modules")
    op.drop_table("plans")
