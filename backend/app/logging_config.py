"""Structured logging configuration with correlation IDs."""
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable for request correlation ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request correlation ID."""
    return request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set the request correlation ID. Generates one if not provided."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def add_request_id(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add request_id to all log entries."""
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with structlog."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_request_id,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
