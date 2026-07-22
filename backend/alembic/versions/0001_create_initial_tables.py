"""Création initiale des tables — users, sites, metrics_snapshots, page_metrics.

Revision ID: 0001
Revises: 
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crée toutes les tables de l'application."""

    # ------------------------------------------------------------------
    # Table : users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # Table : sites
    # ------------------------------------------------------------------
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("ga4_property_id", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("healthy", "warning", "offline", "error", name="site_status"),
            server_default="healthy",
            nullable=False,
        ),
        sa.Column("health_score", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sites")),
        sa.UniqueConstraint("url", name=op.f("uq_sites_url")),
        sa.UniqueConstraint("ga4_property_id", name=op.f("uq_sites_ga4_property_id")),
    )

    # ------------------------------------------------------------------
    # Table : metrics_snapshots
    # ------------------------------------------------------------------
    op.create_table(
        "metrics_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=False),
        sa.Column("users", sa.Integer(), nullable=False),
        sa.Column("new_users", sa.Integer(), nullable=False),
        sa.Column("page_views", sa.Integer(), nullable=False),
        sa.Column("bounce_rate", sa.Float(), nullable=False),
        sa.Column("avg_session_duration", sa.Float(), nullable=False),
        sa.Column("traffic_organic", sa.Float(), nullable=False),
        sa.Column("traffic_direct", sa.Float(), nullable=False),
        sa.Column("traffic_social", sa.Float(), nullable=False),
        sa.Column("traffic_referral", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name=op.f("fk_metrics_snapshots_site_id_sites"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_metrics_snapshots")),
        sa.UniqueConstraint(
            "site_id", "snapshot_date", name="uq_metrics_site_date"
        ),
    )
    op.create_index(
        op.f("ix_metrics_snapshots_site_id"),
        "metrics_snapshots", ["site_id"], unique=False,
    )
    op.create_index(
        op.f("ix_metrics_snapshots_snapshot_date"),
        "metrics_snapshots", ["snapshot_date"], unique=False,
    )

    # ------------------------------------------------------------------
    # Table : page_metrics
    # ------------------------------------------------------------------
    op.create_table(
        "page_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("page_date", sa.Date(), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("page_views", sa.Integer(), nullable=False),
        sa.Column("traffic_pct", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name=op.f("fk_page_metrics_site_id_sites"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_page_metrics")),
        sa.UniqueConstraint(
            "site_id", "page_date", "path", name="uq_page_site_date_path"
        ),
    )
    op.create_index(
        op.f("ix_page_metrics_site_id"),
        "page_metrics", ["site_id"], unique=False,
    )
    op.create_index(
        op.f("ix_page_metrics_page_date"),
        "page_metrics", ["page_date"], unique=False,
    )


def downgrade() -> None:
    """Supprime toutes les tables (dans l'ordre inverse des FK)."""
    op.drop_index(op.f("ix_page_metrics_page_date"), table_name="page_metrics")
    op.drop_index(op.f("ix_page_metrics_site_id"), table_name="page_metrics")
    op.drop_table("page_metrics")

    op.drop_index(op.f("ix_metrics_snapshots_snapshot_date"), table_name="metrics_snapshots")
    op.drop_index(op.f("ix_metrics_snapshots_site_id"), table_name="metrics_snapshots")
    op.drop_table("metrics_snapshots")

    op.drop_table("sites")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Supprime l'enum PostgreSQL
    sa.Enum(name="site_status").drop(op.get_bind(), checkfirst=True)
