"""Deterministic mastery calculation engine for RootLearn.

This service implements deterministic formulas for calculating mastery scores
and confidence from evidence. No AI is involved in these calculations.
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models import Concept, ConceptEdge, DiagnosticAttempt, MasteryEvent, TeachBackAttempt

logger = get_logger(__name__)


@dataclass
class Evidence:
    """Evidence data for mastery update."""
    
    source_type: Literal["diagnostic", "tutoring", "teachback", "manual"]
    reason: dict


class MasteryStatus(str, Enum):
    """Mastery status bands based on score thresholds."""
    
    WEAK = "weak"  # 0.00 - 0.39
    LEARNING = "learning"  # 0.40 - 0.69
    UNDERSTOOD = "understood"  # 0.70 - 0.84
    MASTERED = "mastered"  # 0.85 - 1.00
    LOCKED = "locked"  # Prerequisites not met


class MasteryService:
    """Deterministic mastery calculation service.
    
    This service calculates mastery scores using deterministic formulas:
    - Mastery: weighted combination of diagnostic, practice, and teach-back evidence
    - Confidence: based on evidence quantity and consistency
    - Status: mapped from mastery score to bands
    - Locking: based on prerequisite mastery thresholds
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10
    """

    # Evidence type weights for mastery calculation
    DIAGNOSTIC_WEIGHT = Decimal("0.45")
    PRACTICE_WEIGHT = Decimal("0.35")
    TEACHBACK_WEIGHT = Decimal("0.20")
    
    # Mastery status thresholds
    WEAK_THRESHOLD = Decimal("0.40")
    LEARNING_THRESHOLD = Decimal("0.70")
    UNDERSTOOD_THRESHOLD = Decimal("0.85")
    
    # Locking threshold
    PREREQUISITE_MASTERY_THRESHOLD = Decimal("0.70")
    
    # Confidence mapping by evidence count
    CONFIDENCE_MAP = {
        0: Decimal("0.10"),
        1: Decimal("0.35"),
        2: Decimal("0.60"),
        3: Decimal("0.80"),
    }
    DEFAULT_CONFIDENCE = Decimal("0.90")  # For 4+ evidence items

    def __init__(self, db: AsyncSession):
        """Initialize mastery service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def calculate_mastery(self, concept_id: uuid.UUID) -> float:
        """Calculate mastery score for a concept using deterministic formula.
        
        Uses weighted combination of evidence:
        - Diagnostic: 45%
        - Practice (tutoring): 35%
        - Teach-back: 20%
        
        When partial evidence exists, weights are renormalized to sum to 1.0.
        
        Args:
            concept_id: ID of the concept to calculate mastery for
            
        Returns:
            Mastery score in range [0.0, 1.0]
            
        Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
        """
        # Get diagnostic evidence
        diagnostic_result = await self.db.execute(
            select(DiagnosticAttempt)
            .where(DiagnosticAttempt.concept_id == concept_id)
            .order_by(DiagnosticAttempt.created_at.desc())
        )
        diagnostic_attempts = diagnostic_result.scalars().all()
        
        # Get teach-back evidence
        teachback_result = await self.db.execute(
            select(TeachBackAttempt)
            .where(TeachBackAttempt.concept_id == concept_id)
            .order_by(TeachBackAttempt.created_at.desc())
        )
        teachback_attempts = teachback_result.scalars().all()
        
        # For MVP, practice evidence comes from tutoring interactions
        # We'll use a placeholder of 0.0 for now (will be implemented in task 12)
        practice_score: Decimal | None = None
        
        # Calculate average scores for each evidence type
        diagnostic_score: Decimal | None = None
        if diagnostic_attempts:
            # Average correctness and reasoning scores
            scores = [
                (attempt.correctness_score + attempt.reasoning_score) / Decimal("2")
                for attempt in diagnostic_attempts
            ]
            diagnostic_score = sum(scores, Decimal("0")) / Decimal(len(scores))
        
        teachback_score: Decimal | None = None
        if teachback_attempts:
            # Average coverage, reasoning, and clarity scores
            scores = [
                (attempt.coverage_score + attempt.reasoning_score + attempt.clarity_score) / Decimal("3")
                for attempt in teachback_attempts
            ]
            teachback_score = sum(scores, Decimal("0")) / Decimal(len(scores))
        
        # Build weights dictionary with available evidence
        available_weights = {}
        if diagnostic_score is not None:
            available_weights["diagnostic"] = (self.DIAGNOSTIC_WEIGHT, diagnostic_score)
        if practice_score is not None:
            available_weights["practice"] = (self.PRACTICE_WEIGHT, practice_score)
        if teachback_score is not None:
            available_weights["teachback"] = (self.TEACHBACK_WEIGHT, teachback_score)
        
        # If no evidence, return 0.0
        if not available_weights:
            return 0.0
        
        # Renormalize weights to sum to 1.0
        total_weight = sum(w for w, _ in available_weights.values())
        
        # Calculate weighted mastery
        mastery = Decimal("0")
        for weight, score in available_weights.values():
            normalized_weight = weight / total_weight
            mastery += normalized_weight * score
        
        # Ensure bounds [0.0, 1.0]
        mastery = max(Decimal("0"), min(Decimal("1"), mastery))
        
        logger.debug(
            "mastery_calculated",
            concept_id=str(concept_id),
            diagnostic_score=float(diagnostic_score) if diagnostic_score else None,
            practice_score=float(practice_score) if practice_score else None,
            teachback_score=float(teachback_score) if teachback_score else None,
            mastery=float(mastery),
        )
        
        return float(mastery)

    async def calculate_confidence(self, concept_id: uuid.UUID) -> float:
        """Calculate confidence score based on evidence quantity.
        
        Confidence mapping:
        - 0 evidence: 0.10
        - 1 evidence: 0.35
        - 2 evidence: 0.60
        - 3 evidence: 0.80
        - 4+ evidence: 0.90
        
        Args:
            concept_id: ID of the concept to calculate confidence for
            
        Returns:
            Confidence score in range [0.0, 1.0]
            
        Requirements: 6.8
        """
        # Count all evidence types
        diagnostic_result = await self.db.execute(
            select(DiagnosticAttempt)
            .where(DiagnosticAttempt.concept_id == concept_id)
        )
        diagnostic_count = len(diagnostic_result.scalars().all())
        
        teachback_result = await self.db.execute(
            select(TeachBackAttempt)
            .where(TeachBackAttempt.concept_id == concept_id)
        )
        teachback_count = len(teachback_result.scalars().all())
        
        # Total evidence count (will add tutoring when implemented)
        total_evidence = diagnostic_count + teachback_count
        
        # Map to confidence
        confidence = self.CONFIDENCE_MAP.get(total_evidence, self.DEFAULT_CONFIDENCE)
        
        logger.debug(
            "confidence_calculated",
            concept_id=str(concept_id),
            evidence_count=total_evidence,
            confidence=float(confidence),
        )
        
        return float(confidence)

    def get_mastery_status(self, mastery: float) -> MasteryStatus:
        """Map mastery score to status band.
        
        Status bands:
        - weak: [0.00, 0.40)
        - learning: [0.40, 0.70)
        - understood: [0.70, 0.85)
        - mastered: [0.85, 1.00]
        
        Args:
            mastery: Mastery score in range [0.0, 1.0]
            
        Returns:
            MasteryStatus enum value
            
        Requirements: 6.9
        """
        mastery_decimal = Decimal(str(mastery))
        
        if mastery_decimal < self.WEAK_THRESHOLD:
            return MasteryStatus.WEAK
        elif mastery_decimal < self.LEARNING_THRESHOLD:
            return MasteryStatus.LEARNING
        elif mastery_decimal < self.UNDERSTOOD_THRESHOLD:
            return MasteryStatus.UNDERSTOOD
        else:
            return MasteryStatus.MASTERED

    async def is_concept_locked(self, concept_id: uuid.UUID) -> bool:
        """Check if a concept is locked due to unmet prerequisites.
        
        A concept is locked if any of its prerequisites have mastery < 0.70.
        
        Args:
            concept_id: ID of the concept to check
            
        Returns:
            True if concept is locked, False otherwise
            
        Requirements: 6.10
        """
        # Get all incoming edges (prerequisites) for this concept
        edges_result = await self.db.execute(
            select(ConceptEdge)
            .where(ConceptEdge.target_concept_id == concept_id)
        )
        prerequisite_edges = edges_result.scalars().all()
        
        # If no prerequisites, not locked
        if not prerequisite_edges:
            logger.debug(
                "concept_not_locked_no_prerequisites",
                concept_id=str(concept_id),
            )
            return False
        
        # Check each prerequisite's mastery
        for edge in prerequisite_edges:
            prereq_result = await self.db.execute(
                select(Concept).where(Concept.id == edge.source_concept_id)
            )
            prerequisite = prereq_result.scalar_one()
            
            if prerequisite.mastery_score < self.PREREQUISITE_MASTERY_THRESHOLD:
                logger.debug(
                    "concept_locked_prerequisite_not_met",
                    concept_id=str(concept_id),
                    prerequisite_id=str(prerequisite.id),
                    prerequisite_mastery=float(prerequisite.mastery_score),
                    threshold=float(self.PREREQUISITE_MASTERY_THRESHOLD),
                )
                return True
        
        logger.debug(
            "concept_not_locked_prerequisites_met",
            concept_id=str(concept_id),
        )
        return False

    async def update_concept_lock_status(self, concept_id: uuid.UUID) -> None:
        """Update a concept's lock status based on prerequisites.
        
        Sets concept status to "locked" if prerequisites are not met,
        otherwise leaves status unchanged.
        
        Args:
            concept_id: ID of the concept to update
            
        Requirements: 6.10
        """
        is_locked = await self.is_concept_locked(concept_id)
        
        concept_result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        concept = concept_result.scalar_one()
        
        if is_locked and concept.status != MasteryStatus.LOCKED.value:
            old_status = concept.status
            concept.status = MasteryStatus.LOCKED.value
            await self.db.flush()
            
            logger.info(
                "concept_locked",
                concept_id=str(concept_id),
                old_status=old_status,
                new_status=concept.status,
            )
        elif not is_locked and concept.status == MasteryStatus.LOCKED.value:
            # Unlock and set status based on mastery
            mastery_status = self.get_mastery_status(float(concept.mastery_score))
            concept.status = mastery_status.value
            await self.db.flush()
            
            logger.info(
                "concept_unlocked",
                concept_id=str(concept_id),
                new_status=concept.status,
            )

    async def update_mastery(
        self,
        concept_id: uuid.UUID,
        evidence: Evidence,
    ) -> MasteryEvent:
        """Update mastery score and create audit event.
        
        Calculates new mastery and confidence, updates the concept,
        and creates a mastery_events record for audit trail.
        
        Args:
            concept_id: ID of the concept to update
            evidence: Evidence containing source_type and reason
            
        Returns:
            Created MasteryEvent model
            
        Requirements: 7.1, 7.2
        """
        # Get current concept state
        concept_result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        concept = concept_result.scalar_one()
        
        # Store old values
        old_mastery = float(concept.mastery_score)
        old_confidence = float(concept.confidence_score)
        old_status = concept.status
        
        # Calculate new values
        new_mastery = await self.calculate_mastery(concept_id)
        new_confidence = await self.calculate_confidence(concept_id)
        
        # Update concept
        concept.mastery_score = Decimal(str(new_mastery))
        concept.confidence_score = Decimal(str(new_confidence))
        
        # Update status based on new mastery (unless locked)
        is_locked = await self.is_concept_locked(concept_id)
        if is_locked:
            concept.status = MasteryStatus.LOCKED.value
        else:
            mastery_status = self.get_mastery_status(new_mastery)
            concept.status = mastery_status.value
        
        await self.db.flush()
        
        # Create mastery event
        mastery_event = MasteryEvent(
            session_id=concept.session_id,
            concept_id=concept_id,
            source_type=evidence.source_type,
            old_score=Decimal(str(old_mastery)),
            new_score=Decimal(str(new_mastery)),
            old_confidence=Decimal(str(old_confidence)),
            new_confidence=Decimal(str(new_confidence)),
            reason_json=evidence.reason,
        )
        
        self.db.add(mastery_event)
        await self.db.flush()
        await self.db.refresh(mastery_event)
        
        logger.info(
            "mastery_updated",
            concept_id=str(concept_id),
            old_mastery=old_mastery,
            new_mastery=new_mastery,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            old_status=old_status,
            new_status=concept.status,
            source_type=evidence.source_type,
        )
        
        return mastery_event

