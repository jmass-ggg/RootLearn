"""Custom exceptions for RootLearn application."""
from typing import Any, Optional


class RootLearnException(Exception):
    """Base exception for all RootLearn errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        """Initialize exception.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(RootLearnException):
    """Input validation failed."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=400,
            details=details,
        )


class NotFoundError(RootLearnException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            code=f"{resource.lower().replace(' ', '_')}_not_found",
            status_code=404,
            details={"identifier": identifier},
        )


class UnauthorizedError(RootLearnException):
    """Authentication required."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code="unauthorized",
            status_code=401,
        )


class ForbiddenError(RootLearnException):
    """Insufficient permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code="forbidden",
            status_code=403,
        )


class ConflictError(RootLearnException):
    """Resource conflict (e.g., duplicate)."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="conflict",
            status_code=409,
            details=details,
        )


class AIProviderError(RootLearnException):
    """AI provider error."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        details: Optional[dict[str, Any]] = None,
    ):
        details = details or {}
        details["provider"] = provider
        super().__init__(
            message=message,
            code="ai_provider_error",
            status_code=503,
            details=details,
        )


class GraphValidationError(RootLearnException):
    """Graph validation failed."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="graph_validation_error",
            status_code=400,
            details=details,
        )


class DatabaseError(RootLearnException):
    """Database operation failed."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            code="database_error",
            status_code=500,
        )


class RateLimitError(RootLearnException):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: int,
        limit: int,
        details: Optional[dict[str, Any]] = None,
    ):
        details = details or {}
        details.update({
            "retry_after_seconds": retry_after,
            "limit": limit,
        })
        super().__init__(
            message=message,
            code="rate_limit_exceeded",
            status_code=429,
            details=details,
        )


class StateTransitionError(RootLearnException):
    """Invalid session state transition."""
    
    def __init__(
        self,
        current_state: str,
        requested_state: str,
    ):
        super().__init__(
            message=f"Cannot transition from {current_state} to {requested_state}",
            code="invalid_state_transition",
            status_code=400,
            details={
                "current_state": current_state,
                "requested_state": requested_state,
            },
        )
