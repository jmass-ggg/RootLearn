"""Concept analysis service for RootLearn.

This service handles target concept identification from learner prompts.
It uses AI to extract and normalize the concept the learner wants to understand.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import (
    CONCEPT_ANALYSIS_SYSTEM_PROMPT,
    CONCEPT_ANALYSIS_VERSION,
    get_concept_analysis_user_prompt,
)
from app.ai.schemas import ConceptAnalysisOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.models import Concept, LearningSession


class ConceptService:
    """Service for concept analysis and management."""

    def __init__(self, db: AsyncSession, ai_service: ValidatedAIService):
        """Initialize the concept service.
        
        Args:
            db: Database session
            ai_service: Validated AI service with retry logic
        """
        self.db = db
        self.ai_service = ai_service

    async def analyze_target_concept(
        self,
        session_id: uuid.UUID,
        prompt: str,
    ) -> Concept:
        """Analyze learner prompt and identify target concept.
        
        Uses AI to extract the primary concept from the learner's input,
        normalizes it, and stores it as the target concept for the session.
        
        Args:
            session_id: ID of the learning session
            prompt: Learner's original input describing what they want to learn
            
        Returns:
            Created Concept model marked as target (is_target=True)
            
        Raises:
            ValueError: If session not found
            AIProviderError: On AI provider failures
        """
        # Verify session exists
        result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Call AI to analyze the concept
        system_prompt = CONCEPT_ANALYSIS_SYSTEM_PROMPT
        user_prompt = get_concept_analysis_user_prompt(prompt)
        
        concept_output: ConceptAnalysisOutput = await self.ai_service.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=ConceptAnalysisOutput,
            purpose="target_concept_identification",
            prompt_version=CONCEPT_ANALYSIS_VERSION,
            temperature=0.7,
            session_id=session_id,
        )

        # Create and store the concept
        concept = Concept(
            session_id=session_id,
            slug=concept_output.slug,
            name=concept_output.name,
            description=concept_output.description,
            is_target=True,  # Mark as target concept
            mastery_score=0.0,
            confidence_score=0.1,
            status="unknown",
        )
        
        self.db.add(concept)
        
        # Update session with normalized topic and target concept reference
        session.normalized_topic = concept_output.domain
        session.target_concept_id = concept.id
        
        await self.db.commit()
        await self.db.refresh(concept)
        
        return concept

    async def get_concept(self, concept_id: uuid.UUID) -> Concept | None:
        """Get a concept by ID.
        
        Args:
            concept_id: ID of the concept to retrieve
            
        Returns:
            Concept model or None if not found
        """
        result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        return result.scalar_one_or_none()

    async def get_target_concept(self, session_id: uuid.UUID) -> Concept | None:
        """Get the target concept for a session.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            Target Concept model or None if not found
        """
        result = await self.db.execute(
            select(Concept)
            .where(Concept.session_id == session_id)
            .where(Concept.is_target == True)  # noqa: E712
        )
        return result.scalar_one_or_none()
