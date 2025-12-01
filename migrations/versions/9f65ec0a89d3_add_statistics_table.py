from alembic import op
import sqlalchemy as sa

"""add statistics table"""

revision = "9f65ec0a89d3"
down_revision = "f5830da0142f"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("games", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("games_won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duels", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duels_won", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("statistics")