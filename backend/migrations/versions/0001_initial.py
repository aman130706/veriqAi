from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    # Models are created by app startup for the local MVP. Generate a full migration
    # with `alembic revision --autogenerate -m "initial"` for production workflows.
    pass
def downgrade():
    pass
