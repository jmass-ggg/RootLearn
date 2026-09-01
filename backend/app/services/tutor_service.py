"""Socratic tutoring service for RootLearn.

This service provides adaptive Socratic tutoring for root gap concepts using
AI to generate guiding questions and progressive hints.

Requirements: 9.1, 9.2, 9.3, 9.5, 9.6, 9.8
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_provider
from app.ai.logging_service_temp import AILoggingService
from app.ai.prompts import (
    SOCRATIC_TUTOR_SYSTEM_PROMPT,
    SOCRATIC_TUTOR_VERSION,
    get_socratic_tutor_user_prompt,
)
from app.logging_config import get_logger
from app.models import Concept, ConceptEdge, DiagnosticAttempt, LearningSession, TutorMessage
from app.services.mastery_service import Evidence, MasteryService

logger = get_logger(__name__)


@dataclass
class TutorContext:
    """Context data for Socratic tutoring."""
    
    current_concept: Concept
    target_concept: Concept
    root_gap_explanation: str
    recent_messages: list[dict]
    misconceptions: list[str]
    mastery_score: float
    confidence_score: float
    hint_level: int
    graph_neighborhood: list[dict]


class TutorService:
    """Service for Socratic tutoring.
    
    This service generates tutoring responses using AI with progressive hint
    escalation, manages conversation history, and updates practice evidence.
    """
    
    # Hint level escalation thresholds
    MAX_HINT_LEVEL = 4
    MESSAGES_BEFORE_ESCALATION = 3

    def __init__(self, db: AsyncSession):
        """Initialize tutor service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.ai_logging_service = AILoggingService(db)
        self.mastery_service = MasteryService(db)

    async def start_tutoring(
        self,
        session_id: uuid.UUID,
        concept_id: uuid.UUID,
    ) -> None:
        """Start tutoring for a concept.
        
        Updates session status to "tutoring" and prepares for tutoring session.
        
        Args:
            session_id: ID of the learning session
            concept_id: ID of the concept to tutor (root gap)
            
        Raises:
            ValueError: If session or concept not found
            
        Requirements: 9.1
        """
        # Get session
        session_result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Verify concept exists and belongs to session
        concept_result = await self.db.execute(
            select(Concept).where(
                Concept.id == concept_id,
                Concept.session_id == session_id,
            )
        )
        concept = concept_result.scalar_one_or_none()
        
        if not concept:
            raise ValueError(f"Concept {concept_id} not found in session {session_id}")
        
        # Update session status to tutoring
        session.status = "tutoring"
        await self.db.flush()
        
        logger.info(
            "tutoring_started",
            session_id=str(session_id),
            concept_id=str(concept_id),
            concept_name=concept.name,
        )

    async def get_tutor_context(self, session_id: uuid.UUID) -> TutorContext:
        """Get context data for tutoring.
        
        Assembles all necessary context for generating tutor responses:
        - Current concept (root gap)
        - Target concept
        - Root gap explanation
        - Recent conversation messages
        - Known misconceptions
        - Mastery and confidence
        - Current hint level
        - Related concepts from graph
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            TutorContext with all context data
            
        Raises:
            ValueError: If session or required data not found
            
        Requirements: 9.5
        """
        # Get session
        session_result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.target_concept_id:
            raise ValueError(f"Session {session_id} has no target concept")
        
        # Get target concept
        target_result = await self.db.execute(
            select(Concept).where(Concept.id == session.target_concept_id)
        )
        target_concept = target_result.scalar_one_or_none()
        
        if not target_concept:
            raise ValueError(f"Target concept not found")
        
        # Find current concept being tutored (most recent tutor message)
        messages_result = await self.db.execute(
            select(TutorMessage)
            .where(TutorMessage.session_id == session_id)
            .order_by(TutorMessage.created_at.desc())
            .limit(1)
        )
        recent_message = messages_result.scalar_one_or_none()
        
        if not recent_message:
            raise ValueError("No tutoring messages found. Call start_tutoring first.")
        
        current_concept_id = recent_message.concept_id
        
        # Get current concept
        current_result = await self.db.execute(
            select(Concept).where(Concept.id == current_concept_id)
        )
        current_concept = current_result.scalar_one_or_none()
        
        if not current_concept:
            raise ValueError(f"Current concept {current_concept_id} not found")
        
        # Get recent messages for this concept (last 10)
        all_messages_result = await self.db.execute(
            select(TutorMessage)
            .where(
                TutorMessage.session_id == session_id,
                TutorMessage.concept_id == current_concept_id,
            )
            .order_by(TutorMessage.created_at.asc())
        )
        all_messages = all_messages_result.scalars().all()
        
        recent_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages[-10:]  # Last 10 messages
        ]
        
        # Get current hint level (highest hint_level from assistant messages)
        hint_level = 0
        for msg in all_messages:
            if msg.role == "assistant" and msg.hint_level is not None:
                hint_level = max(hint_level, msg.hint_level)
        
        # Get misconceptions from diagnostic attempts
        diagnostic_result = await self.db.execute(
            select(DiagnosticAttempt)
            .where(DiagnosticAttempt.concept_id == current_concept_id)
            .order_by(DiagnosticAttempt.created_at.desc())
        )
        diagnostic_attempts = diagnostic_result.scalars().all()
        
        misconceptions = []
        for attempt in diagnostic_attempts:
            if attempt.misconceptions_json and isinstance(attempt.misconceptions_json, list):
                misconceptions.extend(attempt.misconceptions_json)
        
        # Remove duplicates while preserving order
        seen = set()
        misconceptions = [
            m for m in misconceptions
            if not (m in seen or seen.add(m))  # type: ignore
        ]
        
        # Get mastery and confidence
        mastery_score = float(current_concept.mastery_score)
        confidence_score = float(current_concept.confidence_score)
        
        # Build graph neighborhood (related concepts)
        # Get all concepts and edges
        concepts_result = await self.db.execute(
            select(Concept).where(Concept.session_id == session_id)
        )
        all_concepts = concepts_result.scalars().all()
        
        edges_result = await self.db.execute(
            select(ConceptEdge).where(ConceptEdge.session_id == session_id)
        )
        edges = edges_result.scalars().all()
        
        # Build graph
        G = nx.DiGraph()
        concept_map = {c.id: c for c in all_concepts}
        
        for concept in all_concepts:
            G.add_node(concept.id)
        
        for edge in edges:
            G.add_edge(edge.source_concept_id, edge.target_concept_id)
        
        # Get neighborhood: predecessors and successors
        neighbors = set()
        try:
            neighbors.update(G.predecessors(current_concept_id))
            neighbors.update(G.successors(current_concept_id))
        except nx.NetworkXError:
            pass
        
        graph_neighborhood = [
            {
                "name": concept_map[neighbor_id].name,
                "description": concept_map[neighbor_id].description,
            }
            for neighbor_id in neighbors
            if neighbor_id in concept_map
        ]
        
        # Generate root gap explanation
        from app.services.root_gap_service import RootGapService
        
        root_gap_service = RootGapService(self.db)
        
        # Calculate gap score for explanation
        gap_score = await root_gap_service.calculate_gap_score(
            concept_id=current_concept_id,
            graph=G,
            target_concept_id=target_concept.id,
            concept_map=concept_map,
            edges=edges,
        )
        
        gap_explanation = await root_gap_service.explain_gap(
            concept_id=current_concept_id,
            gap_score=gap_score,
            graph=G,
            target_concept_id=target_concept.id,
            concept_map=concept_map,
            edges=edges,
        )
        
        root_gap_explanation = "; ".join(gap_explanation.reasons)
        
        context = TutorContext(
            current_concept=current_concept,
            target_concept=target_concept,
            root_gap_explanation=root_gap_explanation,
            recent_messages=recent_messages,
            misconceptions=misconceptions,
            mastery_score=mastery_score,
            confidence_score=confidence_score,
            hint_level=hint_level,
            graph_neighborhood=graph_neighborhood,
        )
        
        logger.debug(
            "tutor_context_assembled",
            session_id=str(session_id),
            current_concept=current_concept.name,
            target_concept=target_concept.name,
            hint_level=hint_level,
            message_count=len(recent_messages),
            misconception_count=len(misconceptions),
        )
        
        return context

    async def generate_response(
        self,
        session_id: uuid.UUID,
        user_message: str,
    ) -> str:
        """Generate Socratic tutor response to user message.
        
        Uses AI to generate a response based on:
        - Current concept being taught
        - Conversation history
        - Known misconceptions
        - Current mastery level
        - Progressive hint level
        
        Stores both user message and AI response in database.
        
        Args:
            session_id: ID of the learning session
            user_message: The learner's message/question
            
        Returns:
            AI-generated tutor response
            
        Raises:
            ValueError: If session or context not found
            
        Requirements: 9.2, 9.5, 9.6
        """
        # Get tutor context
        context = await self.get_tutor_context(session_id)
        
        # Store user message
        user_msg = TutorMessage(
            session_id=session_id,
            concept_id=context.current_concept.id,
            role="user",
            content=user_message,
            hint_level=None,  # User messages don't have hint levels
        )
        self.db.add(user_msg)
        await self.db.flush()
        
        # Update recent messages to include new user message
        context.recent_messages.append({
            "role": "user",
            "content": user_message,
        })
        
        # Generate AI response
        provider = get_ai_provider()
        
        # Build prompt
        system_prompt = SOCRATIC_TUTOR_SYSTEM_PROMPT
        user_prompt = get_socratic_tutor_user_prompt(
            current_concept_name=context.current_concept.name,
            current_concept_description=context.current_concept.description,
            target_concept_name=context.target_concept.name,
            root_gap_explanation=context.root_gap_explanation,
            recent_messages=context.recent_messages,
            misconceptions=context.misconceptions,
            mastery_score=context.mastery_score,
            confidence_score=context.confidence_score,
            hint_level=context.hint_level,
            graph_neighborhood=context.graph_neighborhood,
        )
        
        # Log AI invocation start
        ai_run = await self.ai_logging_service.log_ai_invocation(
            session_id=session_id,
            purpose="socratic_tutoring",
            prompt_version=SOCRATIC_TUTOR_VERSION,
            input_data={
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "concept_id": str(context.current_concept.id),
                "hint_level": context.hint_level,
            },
        )
        
        try:
            # Generate response using stream_text (for MVP, we'll collect it)
            response_chunks = []
            async for chunk in provider.stream_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            ):
                response_chunks.append(chunk)
            
            assistant_response = "".join(response_chunks)
            
            # Log success
            await self.ai_logging_service.log_ai_completion(
                ai_run_id=ai_run.id,
                output_data={"response": assistant_response},
                success=True,
            )
            
            # Store assistant message
            assistant_msg = TutorMessage(
                session_id=session_id,
                concept_id=context.current_concept.id,
                role="assistant",
                content=assistant_response,
                hint_level=context.hint_level,
                ai_run_id=ai_run.id,
            )
            self.db.add(assistant_msg)
            await self.db.flush()
            
            logger.info(
                "tutor_response_generated",
                session_id=str(session_id),
                concept_id=str(context.current_concept.id),
                hint_level=context.hint_level,
                response_length=len(assistant_response),
            )
            
            # Update practice evidence based on interaction
            await self._update_practice_evidence(
                concept_id=context.current_concept.id,
                user_message=user_message,
                assistant_response=assistant_response,
            )
            
            return assistant_response
        
        except Exception as e:
            # Log failure
            await self.ai_logging_service.log_ai_completion(
                ai_run_id=ai_run.id,
                output_data=None,
                success=False,
                error_code=type(e).__name__,
            )
            
            logger.error(
                "tutor_response_generation_failed",
                session_id=str(session_id),
                concept_id=str(context.current_concept.id),
                error=str(e),
            )
            raise

    async def escalate_hint_level(self, session_id: uuid.UUID) -> int:
        """Escalate hint level for tutoring session.
        
        Increases the hint level to provide stronger guidance when the
        learner is struggling. Maximum hint level is 4.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            New hint level
            
        Raises:
            ValueError: If session not found
            
        Requirements: 9.3
        """
        # Get current context to find hint level
        context = await self.get_tutor_context(session_id)
        
        # Increment hint level (max 4)
        new_hint_level = min(context.hint_level + 1, self.MAX_HINT_LEVEL)
        
        logger.info(
            "hint_level_escalated",
            session_id=str(session_id),
            concept_id=str(context.current_concept.id),
            old_level=context.hint_level,
            new_level=new_hint_level,
        )
        
        return new_hint_level

    async def _update_practice_evidence(
        self,
        concept_id: uuid.UUID,
        user_message: str,
        assistant_response: str,
    ) -> None:
        """Update practice evidence from tutoring interaction.
        
        Heuristic scoring based on interaction quality:
        - Long, thoughtful user responses indicate engagement
        - Hints at higher levels suggest struggle
        - Progressive improvement over multiple interactions
        
        For MVP, we use a simple heuristic. A more sophisticated
        approach could use AI to evaluate understanding demonstrated
        in the conversation.
        
        Args:
            concept_id: ID of the concept being tutored
            user_message: The learner's message
            assistant_response: The tutor's response
            
        Requirements: 9.8
        """
        # Get current context to check hint level
        # Count tutor messages for this concept to gauge progress
        messages_result = await self.db.execute(
            select(TutorMessage)
            .where(
                TutorMessage.concept_id == concept_id,
                TutorMessage.role == "user",
            )
        )
        user_messages = messages_result.scalars().all()
        
        message_count = len(user_messages)
        
        # Get latest hint level
        hint_messages_result = await self.db.execute(
            select(TutorMessage)
            .where(
                TutorMessage.concept_id == concept_id,
                TutorMessage.role == "assistant",
                TutorMessage.hint_level.isnot(None),
            )
            .order_by(TutorMessage.created_at.desc())
            .limit(1)
        )
        latest_hint_msg = hint_messages_result.scalar_one_or_none()
        hint_level = latest_hint_msg.hint_level if latest_hint_msg else 0
        
        # Simple heuristic scoring
        # Start with base score
        practice_score = Decimal("0.50")
        
        # Adjust based on hint level (lower is better)
        if hint_level == 0:
            practice_score += Decimal("0.20")  # Minimal hints = good understanding
        elif hint_level == 1:
            practice_score += Decimal("0.10")
        elif hint_level == 2:
            practice_score += Decimal("0.00")
        elif hint_level == 3:
            practice_score -= Decimal("0.10")
        else:  # hint_level 4
            practice_score -= Decimal("0.20")  # Direct explanation needed = struggle
        
        # Adjust based on engagement (message length as proxy)
        if len(user_message) > 100:
            practice_score += Decimal("0.10")  # Thoughtful response
        elif len(user_message) < 20:
            practice_score -= Decimal("0.05")  # Minimal engagement
        
        # Adjust based on interaction count (more practice = better)
        if message_count >= 5:
            practice_score += Decimal("0.10")
        
        # Ensure bounds [0.0, 1.0]
        practice_score = max(Decimal("0.0"), min(Decimal("1.0"), practice_score))
        
        # For now, we'll update mastery after every few interactions
        # to avoid excessive mastery updates
        if message_count % 3 == 0 and message_count > 0:
            evidence = Evidence(
                source_type="tutoring",
                reason={
                    "interaction_count": message_count,
                    "hint_level": hint_level,
                    "practice_score": float(practice_score),
                },
            )
            
            await self.mastery_service.update_mastery(
                concept_id=concept_id,
                evidence=evidence,
            )
            
            logger.debug(
                "practice_evidence_updated",
                concept_id=str(concept_id),
                interaction_count=message_count,
                hint_level=hint_level,
                practice_score=float(practice_score),
            )
