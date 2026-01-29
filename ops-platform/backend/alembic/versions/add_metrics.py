"""Add metrics tables

Revision ID: add_metrics
Revises: 
Create Date: 2024-01-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_metrics'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('cpu_usage', sa.Float(), nullable=False),
        sa.Column('memory_usage', sa.Float(), nullable=False),
        sa.Column('disk_usage', sa.Float(), nullable=False),
        sa.Column('network_in', sa.Float(), server_default='0.0'),
        sa.Column('network_out', sa.Float(), server_default='0.0'),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metrics_resource_id', 'metrics', ['resource_id'])
    op.create_index('ix_metrics_timestamp', 'metrics', ['timestamp'])
    
    # Create process_metrics table
    op.create_table(
        'process_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('process_name', sa.String(length=255), nullable=False),
        sa.Column('process_pid', sa.Integer(), nullable=False),
        sa.Column('cpu_percent', sa.Float(), server_default='0.0'),
        sa.Column('memory_percent', sa.Float(), server_default='0.0'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_process_metrics_resource_id', 'process_metrics', ['resource_id'])
    op.create_index('ix_process_metrics_timestamp', 'process_metrics', ['timestamp'])


def downgrade():
    op.drop_table('process_metrics')
    op.drop_table('metrics')
