"""Global error handlers for FastAPI application."""
import re
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError

from app.exceptions import RootLearnException
from app.logging_config import get_logger, get_request_id

logger = get_logger(__name__)

# Sensitive patterns to redact from error messages
SENSITIVE_PATTERNS = [
    re.compile(r"(api[_-]?key|password|secret|token)[\s:=]+[^\s]+", re.IGNORECASE),
    re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE),  # OpenAI keys
    re.compile(r"postgres://[^@]+@", re.IGNORECASE),  # Database URLs
]


def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages.
    
    Args:
        message: Error message that may contain sensitive data
        
    Returns:
        Sanitized error message
    """
    sanitized = message
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


def create_error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response.
    
    Args:
        code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional error details
        
    Returns:
        Standardized error response dictionary
    """
    request_id = get_request_id()
    
    # Sanitize message and details
    sanitized_message = sanitize_error_message(message)
    sanitized_details = {}
    
    if details:
        for key, value in details.items():
            if isinstance(value, str):
                sanitized_details[key] = sanitize_error_message(value)
            else:
                sanitized_details[key] = value
    
    return {
        "error": {
            "code": code,
            "message": sanitized_message,
            "request_id": request_id,
            "details": sanitized_details,
        }
    }


async def rootlearn_exception_handler(
    request: Request,
    exc: RootLearnException,
) -> JSONResponse:
    """Handle RootLearn custom exceptions.
    
    Args:
        request: FastAPI request
        exc: RootLearn exception
        
    Returns:
        JSON response with error details
    """
    logger.error(
        "rootlearn_exception",
        error_code=exc.code,
        error_message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )
    
    response = create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation error
        
    Returns:
        JSON response with validation error details
    """
    # Extract field-level errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        "validation_error",
        errors=errors,
        path=request.url.path,
        method=request.method,
    )
    
    response = create_error_response(
        code="validation_error",
        message="Request validation failed",
        details={"errors": errors},
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response,
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request
        exc: Pydantic validation error
        
    Returns:
        JSON response with validation error details
    """
    # Extract field-level errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        "pydantic_validation_error",
        errors=errors,
        path=request.url.path,
        method=request.method,
    )
    
    response = create_error_response(
        code="validation_error",
        message="Data validation failed",
        details={"errors": errors},
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response,
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Handle database integrity errors.
    
    Args:
        request: FastAPI request
        exc: SQLAlchemy integrity error
        
    Returns:
        JSON response with safe error message
    """
    # Log full error server-side
    logger.error(
        "database_integrity_error",
        error_type=type(exc).__name__,
        error_str=str(exc.orig) if hasattr(exc, "orig") else str(exc),
        path=request.url.path,
        method=request.method,
    )
    
    # Provide safe client-facing message
    message = "Database constraint violation"
    details = {}
    
    # Try to extract constraint name for better error message
    error_str = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    
    if "unique" in error_str.lower():
        message = "Resource already exists"
        details["constraint"] = "unique"
    elif "foreign key" in error_str.lower():
        message = "Referenced resource does not exist"
        details["constraint"] = "foreign_key"
    elif "not null" in error_str.lower():
        message = "Required field is missing"
        details["constraint"] = "not_null"
    
    response = create_error_response(
        code="constraint_violation",
        message=message,
        details=details,
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Any unhandled exception
        
    Returns:
        JSON response with generic error message
    """
    # Log full error with stack trace server-side
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_str=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,  # Include stack trace
    )
    
    # Provide safe generic message to client
    response = create_error_response(
        code="internal_error",
        message="An internal error occurred. Please try again later.",
        details={},
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )
