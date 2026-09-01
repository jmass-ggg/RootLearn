"""Pydantic schemas for AI output validation.

This module defines the structured output schemas that all AI providers
must conform to. These schemas ensure consistent validation regardless of
which AI provider is used.
"""
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ConceptAnalysisOutput(BaseModel):
    """Schema for target concept identification output.
    
    Used when analyzing the learner's initial prompt to identify
    the primary concept they want to learn.
    """

    slug: str = Field(
        ...,
        description="URL-friendly identifier for the concept (e.g., 'recursion')",
        min_length=1,
        max_length=100,
    )
    name: str = Field(
        ...,
        description="Human-readable concept name (e.g., 'Recursion')",
        min_length=1,
        max_length=200,
    )
    domain: str = Field(
        ...,
        description="Subject domain (e.g., 'Computer Science', 'Mathematics')",
        min_length=1,
        max_length=100,
    )
    description: str = Field(
        ...,
        description="Clear explanation of what this concept is",
        min_length=10,
        max_length=1000,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is URL-safe."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()


class PrerequisiteNode(BaseModel):
    """A single node in the prerequisite graph."""

    slug: str = Field(
        ...,
        description="Unique identifier within this graph",
        min_length=1,
        max_length=100,
    )
    name: str = Field(
        ...,
        description="Human-readable concept name",
        min_length=1,
        max_length=200,
    )
    description: str = Field(
        ...,
        description="Explanation of this prerequisite concept",
        min_length=10,
        max_length=1000,
    )


class PrerequisiteEdge(BaseModel):
    """A directed edge in the prerequisite graph.
    
    Edge from source to target means: source is a prerequisite of target.
    """

    source_slug: str = Field(
        ...,
        description="Slug of the prerequisite concept",
        min_length=1,
    )
    target_slug: str = Field(
        ...,
        description="Slug of the dependent concept",
        min_length=1,
    )
    importance_weight: float = Field(
        default=1.0,
        description="Importance of this prerequisite (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    @field_validator("source_slug", "target_slug")
    @classmethod
    def validate_no_self_loop(cls, v: str, info) -> str:
        """Prevent self-loops at the schema level."""
        if info.field_name == "target_slug":
            if "source_slug" in info.data and info.data["source_slug"] == v:
                raise ValueError("source_slug and target_slug cannot be the same (no self-loops)")
        return v


class PrerequisiteGraphOutput(BaseModel):
    """Schema for prerequisite graph generation output.
    
    Defines the complete prerequisite graph for a target concept.
    Must be a directed acyclic graph (DAG).
    """

    target_slug: str = Field(
        ...,
        description="Slug of the target concept this graph is for",
        min_length=1,
    )
    nodes: list[PrerequisiteNode] = Field(
        ...,
        description="All concepts in the prerequisite graph",
        min_length=1,
        max_length=12,  # Requirement 3.2: max 12 nodes
    )
    edges: list[PrerequisiteEdge] = Field(
        ...,
        description="Prerequisite relationships between concepts",
        min_length=0,
    )

    @field_validator("nodes")
    @classmethod
    def validate_unique_slugs(cls, v: list[PrerequisiteNode]) -> list[PrerequisiteNode]:
        """Ensure all node slugs are unique."""
        slugs = [node.slug for node in v]
        if len(slugs) != len(set(slugs)):
            raise ValueError("All node slugs must be unique")
        return v

    @field_validator("edges")
    @classmethod
    def validate_edge_references(cls, v: list[PrerequisiteEdge], info) -> list[PrerequisiteEdge]:
        """Ensure all edges reference valid nodes."""
        if "nodes" not in info.data:
            return v
        
        valid_slugs = {node.slug for node in info.data["nodes"]}
        
        for edge in v:
            if edge.source_slug not in valid_slugs:
                raise ValueError(f"Edge references unknown source: {edge.source_slug}")
            if edge.target_slug not in valid_slugs:
                raise ValueError(f"Edge references unknown target: {edge.target_slug}")
        
        return v

    @field_validator("edges")
    @classmethod
    def validate_no_duplicate_edges(cls, v: list[PrerequisiteEdge]) -> list[PrerequisiteEdge]:
        """Ensure no duplicate edges."""
        edge_pairs = [(edge.source_slug, edge.target_slug) for edge in v]
        if len(edge_pairs) != len(set(edge_pairs)):
            raise ValueError("Duplicate edges detected")
        return v


class DiagnosticQuestionOutput(BaseModel):
    """Schema for diagnostic question generation output.
    
    Generated for a specific concept to assess learner understanding.
    """

    question_text: str = Field(
        ...,
        description="The diagnostic question to ask the learner",
        min_length=10,
        max_length=2000,
    )
    question_type: str = Field(
        ...,
        description="Type of question",
    )
    rubric: dict[str, Any] = Field(
        ...,
        description="Grading rubric with key points and criteria",
    )
    difficulty: float = Field(
        default=0.5,
        description="Estimated difficulty level (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    @field_validator("question_type")
    @classmethod
    def validate_question_type(cls, v: str) -> str:
        """Ensure valid question type."""
        valid_types = {"short_answer", "multiple_choice", "reasoning", "code"}
        if v not in valid_types:
            raise ValueError(f"Question type must be one of: {valid_types}")
        return v

    @field_validator("rubric")
    @classmethod
    def validate_rubric_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure rubric contains content."""
        if not v:
            raise ValueError("Rubric cannot be empty")
        return v


class DiagnosticEvaluationOutput(BaseModel):
    """Schema for diagnostic answer evaluation output.
    
    AI evaluation of a learner's answer against the rubric.
    """

    correctness_score: float = Field(
        ...,
        description="How correct the answer is (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    reasoning_score: float = Field(
        ...,
        description="Quality of reasoning shown (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    demonstrated_points: list[str] = Field(
        default_factory=list,
        description="Key points the learner correctly demonstrated",
    )
    missing_points: list[str] = Field(
        default_factory=list,
        description="Important points the learner missed or misunderstood",
    )
    misconceptions: list[str] = Field(
        default_factory=list,
        description="Misconceptions or errors detected in the answer",
    )


class SocraticResponseOutput(BaseModel):
    """Schema for Socratic tutoring response output.
    
    Generated during tutoring to guide the learner with questions and hints.
    """

    response_text: str = Field(
        ...,
        description="The tutor's response to the learner",
        min_length=1,
        max_length=2000,
    )
    hint_level: int = Field(
        default=1,
        description="Level of hint provided (1=question, 5=explanation)",
        ge=1,
        le=5,
    )
    suggested_next_topic: str | None = Field(
        None,
        description="Optional suggestion for what to explore next",
        max_length=200,
    )


class TeachBackEvaluationOutput(BaseModel):
    """Schema for teach-back evaluation output.
    
    AI evaluation of the learner's explanation of a concept.
    """

    coverage_score: float = Field(
        ...,
        description="Completeness of key ideas covered (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    reasoning_score: float = Field(
        ...,
        description="Logical correctness of explanation (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    clarity_score: float = Field(
        ...,
        description="Communication effectiveness (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    demonstrated_points: list[str] = Field(
        default_factory=list,
        description="Key points correctly explained",
    )
    missing_points: list[str] = Field(
        default_factory=list,
        description="Important points not covered or unclear",
    )
    misconceptions: list[str] = Field(
        default_factory=list,
        description="Misconceptions or errors in the explanation",
    )

    def average_score(self) -> float:
        """Calculate average score across all dimensions."""
        return (self.coverage_score + self.reasoning_score + self.clarity_score) / 3.0

