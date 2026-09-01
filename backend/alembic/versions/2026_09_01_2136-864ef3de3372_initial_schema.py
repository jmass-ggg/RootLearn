"""initial_schema

Revision ID: 864ef3de3372
Revises: 
Create Date: 2026-09-01 21:36:40.615386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '864ef3de3372'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create learning_sessions table
    op.create_table(
        'learning_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('original_prompt', sa.Text(), nullable=False),
        sa.Column('normalized_topic', sa.String(), nullable=True),
        sa.Column('target_concept_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('analyzing', 'diagnosing', 'tutoring', 'teachback', 'completed', 'abandoned')",
            name='ck_learning_sessions_status'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_sessions_user_id', 'learning_sessions', ['user_id'])
    op.create_index('ix_learning_sessions_status', 'learning_sessions', ['status'])
    
    # Create concepts table
    op.create_table(
        'concepts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_target', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('mastery_score', sa.Numeric(5, 4), nullable=False, server_default=sa.text('0.0')),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=False, server_default=sa.text('0.1')),
        sa.Column('status', sa.String(), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            'mastery_score >= 0 AND mastery_score <= 1',
            name='ck_concepts_mastery_score_bounds'
        ),
        sa.CheckConstraint(
            'confidence_score >= 0 AND confidence_score <= 1',
            name='ck_concepts_confidence_score_bounds'
        ),
        sa.CheckConstraint(
            "status IN ('unknown', 'weak', 'learning', 'understood', 'mastered', 'locked')",
            name='ck_concepts_status'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'slug', name='uq_concepts_session_slug')
    )
    op.create_index('ix_concepts_session_id', 'concepts', ['session_id'])
    op.create_index('ix_concepts_is_target', 'concepts', ['is_target'])
    
    # Add foreign key for target_concept_id in learning_sessions
    op.create_foreign_key(
        'fk_learning_sessions_target_concept_id',
        'learning_sessions',
        'concepts',
        ['target_concept_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create concept_edges table
    op.create_table(
        'concept_edges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('source_concept_id', sa.UUID(), nullable=False),
        sa.Column('target_concept_id', sa.UUID(), nullable=False),
        sa.Column('importance_weight', sa.Numeric(5, 4), nullable=False, server_default=sa.text('1.0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            'source_concept_id != target_concept_id',
            name='ck_concept_edges_no_self_loop'
        ),
        sa.CheckConstraint(
            'importance_weight >= 0 AND importance_weight <= 1',
            name='ck_concept_edges_weight_bounds'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_concept_id', 'target_concept_id', name='uq_concept_edges_source_target')
    )
    op.create_index('ix_concept_edges_session_id', 'concept_edges', ['session_id'])
    op.create_index('ix_concept_edges_source_concept_id', 'concept_edges', ['source_concept_id'])
    op.create_index('ix_concept_edges_target_concept_id', 'concept_edges', ['target_concept_id'])
    
    # Create ai_runs table
    op.create_table(
        'ai_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('prompt_version', sa.String(), nullable=False),
        sa.Column('input_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_code', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_runs_session_id', 'ai_runs', ['session_id'])
    op.create_index('ix_ai_runs_purpose', 'ai_runs', ['purpose'])
    op.create_index('ix_ai_runs_created_at', 'ai_runs', ['created_at'])
    
    # Create diagnostic_questions table
    op.create_table(
        'diagnostic_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('concept_id', sa.UUID(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('rubric_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('difficulty', sa.Numeric(5, 4), nullable=False, server_default=sa.text('0.5')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            "question_type IN ('short_answer', 'multiple_choice', 'reasoning', 'code')",
            name='ck_diagnostic_questions_type'
        ),
        sa.CheckConstraint(
            'difficulty >= 0 AND difficulty <= 1',
            name='ck_diagnostic_questions_difficulty_bounds'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_diagnostic_questions_session_id', 'diagnostic_questions', ['session_id'])
    op.create_index('ix_diagnostic_questions_concept_id', 'diagnostic_questions', ['concept_id'])
    
    # Create diagnostic_attempts table
    op.create_table(
        'diagnostic_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('concept_id', sa.UUID(), nullable=False),
        sa.Column('student_answer', sa.Text(), nullable=False),
        sa.Column('correctness_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('reasoning_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('misconceptions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('missing_points_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            'correctness_score >= 0 AND correctness_score <= 1',
            name='ck_diagnostic_attempts_correctness_bounds'
        ),
        sa.CheckConstraint(
            'reasoning_score >= 0 AND reasoning_score <= 1',
            name='ck_diagnostic_attempts_reasoning_bounds'
        ),
        sa.ForeignKeyConstraint(['question_id'], ['diagnostic_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_run_id'], ['ai_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_diagnostic_attempts_question_id', 'diagnostic_attempts', ['question_id'])
    op.create_index('ix_diagnostic_attempts_session_id', 'diagnostic_attempts', ['session_id'])
    op.create_index('ix_diagnostic_attempts_concept_id', 'diagnostic_attempts', ['concept_id'])
    
    # Create tutor_messages table
    op.create_table(
        'tutor_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('concept_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('hint_level', sa.Integer(), nullable=True),
        sa.Column('ai_run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name='ck_tutor_messages_role'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_run_id'], ['ai_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tutor_messages_session_id', 'tutor_messages', ['session_id'])
    op.create_index('ix_tutor_messages_concept_id', 'tutor_messages', ['concept_id'])
    
    # Create teachback_attempts table
    op.create_table(
        'teachback_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('concept_id', sa.UUID(), nullable=False),
        sa.Column('student_explanation', sa.Text(), nullable=False),
        sa.Column('coverage_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('reasoning_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('clarity_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('misconceptions_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('missing_points_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_run_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            'coverage_score >= 0 AND coverage_score <= 1',
            name='ck_teachback_attempts_coverage_bounds'
        ),
        sa.CheckConstraint(
            'reasoning_score >= 0 AND reasoning_score <= 1',
            name='ck_teachback_attempts_reasoning_bounds'
        ),
        sa.CheckConstraint(
            'clarity_score >= 0 AND clarity_score <= 1',
            name='ck_teachback_attempts_clarity_bounds'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_run_id'], ['ai_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_teachback_attempts_session_id', 'teachback_attempts', ['session_id'])
    op.create_index('ix_teachback_attempts_concept_id', 'teachback_attempts', ['concept_id'])
    
    # Create mastery_events table
    op.create_table(
        'mastery_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('concept_id', sa.UUID(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('old_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('new_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('old_confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('new_confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('reason_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint(
            "source_type IN ('diagnostic', 'tutoring', 'teachback', 'manual')",
            name='ck_mastery_events_source_type'
        ),
        sa.CheckConstraint(
            'old_score >= 0 AND old_score <= 1',
            name='ck_mastery_events_old_score_bounds'
        ),
        sa.CheckConstraint(
            'new_score >= 0 AND new_score <= 1',
            name='ck_mastery_events_new_score_bounds'
        ),
        sa.CheckConstraint(
            'old_confidence >= 0 AND old_confidence <= 1',
            name='ck_mastery_events_old_confidence_bounds'
        ),
        sa.CheckConstraint(
            'new_confidence >= 0 AND new_confidence <= 1',
            name='ck_mastery_events_new_confidence_bounds'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mastery_events_session_id', 'mastery_events', ['session_id'])
    op.create_index('ix_mastery_events_concept_id', 'mastery_events', ['concept_id'])
    op.create_index('ix_mastery_events_created_at', 'mastery_events', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('mastery_events')
    op.drop_table('teachback_attempts')
    op.drop_table('tutor_messages')
    op.drop_table('diagnostic_attempts')
    op.drop_table('diagnostic_questions')
    op.drop_table('ai_runs')
    op.drop_table('concept_edges')
    
    # Drop the foreign key constraint before dropping concepts
    op.drop_constraint('fk_learning_sessions_target_concept_id', 'learning_sessions', type_='foreignkey')
    
    op.drop_table('concepts')
    op.drop_table('learning_sessions')
    op.drop_table('users')
