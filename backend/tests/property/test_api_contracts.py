"""Property-based tests for API contract compliance.

Tests Properties 73-77 from the design document:
- Property 73: Error responses are structured
- Property 74: Errors never expose sensitive data
- Property 75: HTTP status codes are appropriate
- Property 76: Request correlation IDs
- Property 77: Input validation before processing
"""
import re
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from app.exceptions import (
    AIProviderError,
    ConflictError,
    DatabaseError,
    ForbiddenError,
    GraphValidationError,
    NotFoundError,
    RateLimitError,
    StateTransitionError,
    UnauthorizedError,
    ValidationError,
)
from app.main import app

client = TestClient(app)

# Sensitive patterns that should never appear in responses
SENSITIVE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE),  # OpenAI API keys
    re.compile(r"postgres://[^@]*:[^@]*@", re.IGNORECASE),  # Database URLs with credentials
    re.compile(r"(password|secret|api[_-]?key|token)[\s:=]+[\w\-\.]+", re.IGNORECASE),
    re.compile(r"Traceback \(most recent call last\)", re.IGNORECASE),  # Python stack traces
    re.compile(r"at [\w\.]+\(.*:\d+:\d+\)", re.IGNORECASE),  # JavaScript stack traces
]


# Strategy for generating various error types
@st.composite
def error_instance(draw):
    """Generate random RootLearn exception instances."""
    error_type = draw(st.sampled_from([
        ValidationError,
        NotFoundError,
        UnauthorizedError,
        ForbiddenError,
        ConflictError,
        AIProviderError,
        GraphValidationError,
        DatabaseError,
        RateLimitError,
        StateTransitionError,
    ]))
    
    if error_type == ValidationError:
        return ValidationError(
            message=draw(st.text(min_size=1, max_size=100)),
            details={"field": draw(st.text(min_size=1, max_size=50))},
        )
    elif error_type == NotFoundError:
        return NotFoundError(
            resource=draw(st.sampled_from(["Session", "Concept", "Question"])),
            identifier=str(draw(st.uuids())),
        )
    elif error_type == UnauthorizedError:
        return UnauthorizedError()
    elif error_type == ForbiddenError:
        return ForbiddenError()
    elif error_type == ConflictError:
        return ConflictError(
            message=draw(st.text(min_size=1, max_size=100)),
        )
    elif error_type == AIProviderError:
        return AIProviderError(
            message=draw(st.text(min_size=1, max_size=100)),
            provider=draw(st.sampled_from(["openai", "anthropic", "gemini"])),
        )
    elif error_type == GraphValidationError:
        return GraphValidationError(
            message=draw(st.text(min_size=1, max_size=100)),
        )
    elif error_type == DatabaseError:
        return DatabaseError()
    elif error_type == RateLimitError:
        return RateLimitError(
            message=draw(st.text(min_size=1, max_size=100)),
            retry_after=draw(st.integers(min_value=1, max_value=3600)),
            limit=draw(st.integers(min_value=1, max_value=1000)),
        )
    elif error_type == StateTransitionError:
        states = ["analyzing", "diagnosing", "tutoring", "teachback", "completed"]
        return StateTransitionError(
            current_state=draw(st.sampled_from(states)),
            requested_state=draw(st.sampled_from(states)),
        )


# Feature: rootlearn-knowledge-debugger, Property 73: Error responses are structured
@settings(max_examples=100)
@given(error=error_instance())
def test_property_73_error_responses_structured(error):
    """Property 73: Error responses are structured.
    
    For any error response, it should match the schema:
    {error: {code: string, message: string, request_id: string, details: object}}
    
    Validates: Requirements 18.2
    """
    from app.error_handlers import create_error_response
    from app.logging_config import set_request_id
    
    # Set a request ID for the test
    set_request_id()
    
    # Create error response
    response = create_error_response(
        code=error.code,
        message=error.message,
        details=error.details,
    )
    
    # Verify structure
    assert "error" in response
    assert isinstance(response["error"], dict)
    
    error_obj = response["error"]
    assert "code" in error_obj
    assert "message" in error_obj
    assert "request_id" in error_obj
    assert "details" in error_obj
    
    # Verify types
    assert isinstance(error_obj["code"], str)
    assert isinstance(error_obj["message"], str)
    assert isinstance(error_obj["request_id"], str)
    assert isinstance(error_obj["details"], dict)
    
    # Verify code is not empty
    assert len(error_obj["code"]) > 0
    # Verify message is not empty
    assert len(error_obj["message"]) > 0
    # Verify request_id is a valid UUID format
    try:
        uuid.UUID(error_obj["request_id"])
    except ValueError:
        pytest.fail(f"request_id is not a valid UUID: {error_obj['request_id']}")


# Feature: rootlearn-knowledge-debugger, Property 74: Errors never expose sensitive data
@settings(max_examples=100)
@given(
    error_message=st.text(min_size=1, max_size=200),
    api_key=st.from_regex(r"sk-[a-zA-Z0-9]{48}", fullmatch=True),
    password=st.text(min_size=8, max_size=50).filter(lambda x: not x.startswith('\x1b')),
)
def test_property_74_no_sensitive_data_exposure(error_message, api_key, password):
    """Property 74: Errors never expose sensitive data.
    
    For any error response, it should not contain stack traces, API keys,
    raw database errors, or internal prompts.
    
    Validates: Requirements 18.3
    """
    from app.error_handlers import sanitize_error_message
    
    # Create message with sensitive data
    message_with_secrets = (
        f"{error_message} API_KEY={api_key} password={password} "
        f"postgres://user:{password}@host/db"
    )
    
    # Sanitize the message
    sanitized = sanitize_error_message(message_with_secrets)
    
    # Verify API key is removed
    assert api_key not in sanitized, "API key found in sanitized message"
    
    # Verify password pattern is redacted
    assert f"password={password}" not in sanitized or len(password) <= 3, (
        f"Password pattern found in sanitized message: {sanitized}"
    )


# Feature: rootlearn-knowledge-debugger, Property 75: HTTP status codes are appropriate
@settings(max_examples=50)
@given(error=error_instance())
def test_property_75_appropriate_status_codes(error):
    """Property 75: HTTP status codes are appropriate.
    
    For any API response, the HTTP status code should match the response type:
    - 2xx for success
    - 400 for client errors
    - 401 for auth
    - 404 for not found
    - 500 for server errors
    
    Validates: Requirements 18.4
    """
    # Define expected status codes for each error type
    expected_status_codes = {
        ValidationError: 400,
        NotFoundError: 404,
        UnauthorizedError: 401,
        ForbiddenError: 403,
        ConflictError: 409,
        AIProviderError: 503,
        GraphValidationError: 400,
        DatabaseError: 500,
        RateLimitError: 429,
        StateTransitionError: 400,
    }
    
    error_type = type(error)
    expected_code = expected_status_codes.get(error_type, 500)
    
    # Verify the error has the correct status code
    assert error.status_code == expected_code, (
        f"{error_type.__name__} should have status code {expected_code}, "
        f"but has {error.status_code}"
    )
    
    # Verify status code is in valid ranges
    assert 400 <= error.status_code < 600, (
        f"Status code {error.status_code} is not a valid error code"
    )


# Feature: rootlearn-knowledge-debugger, Property 76: Request correlation IDs
@settings(max_examples=100)
@given(
    user_id=st.uuids(),
    prompt=st.text(min_size=10, max_size=100),
)
def test_property_76_request_correlation_ids(user_id, prompt):
    """Property 76: Request correlation IDs.
    
    For any API response (success or error), it should include a unique
    request_id for correlation with logs.
    
    Validates: Requirements 18.5
    """
    # Make a request to create a session
    response = client.post(
        "/api/v1/sessions",
        json={
            "user_id": str(user_id),
            "prompt": prompt,
        },
    )
    
    # Verify X-Request-ID header is present
    assert "X-Request-ID" in response.headers, (
        "Response should include X-Request-ID header"
    )
    
    # Verify it's a valid UUID
    request_id = response.headers["X-Request-ID"]
    try:
        uuid.UUID(request_id)
    except ValueError:
        pytest.fail(f"X-Request-ID is not a valid UUID: {request_id}")
    
    # If there's an error response, verify request_id is in the body too
    if response.status_code >= 400:
        data = response.json()
        # Check if error is at top level or nested in 'detail'
        error_data = data.get("error") or data.get("detail", {}).get("error")
        if error_data:
            assert "request_id" in error_data
            # The request_id in the body should match the header
            assert error_data["request_id"] == request_id


# Feature: rootlearn-knowledge-debugger, Property 77: Input validation before processing
@settings(max_examples=100)
@given(
    user_id=st.one_of(
        st.just("not-a-uuid"),
        st.text(min_size=1, max_size=50),
        st.integers(),
    ),
    prompt=st.one_of(
        st.just(""),  # Empty string
        st.just("   "),  # Whitespace only
        st.text(max_size=0),  # Empty
    ),
)
def test_property_77_input_validation_before_processing(user_id, prompt):
    """Property 77: Input validation before processing.
    
    For any API request with a request body, the input should be validated
    against its schema before any business logic executes.
    
    Validates: Requirements 18.6
    """
    # Make a request with invalid input
    response = client.post(
        "/api/v1/sessions",
        json={
            "user_id": user_id,
            "prompt": prompt,
        },
    )
    
    # Should return 400 Bad Request for validation errors
    assert response.status_code == 400, (
        f"Invalid input should return 400, got {response.status_code}"
    )
    
    # Verify error response structure
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert data["error"]["code"] == "validation_error"
    assert "message" in data["error"]
    assert "details" in data["error"]


# Additional test: Verify error responses never contain raw exceptions
@settings(max_examples=50)
@given(error=error_instance())
def test_no_raw_exception_details_in_response(error):
    """Verify that error responses don't expose raw exception details.
    
    This is an extension of Property 74, specifically checking that
    Python exception details are not leaked.
    """
    from app.error_handlers import create_error_response
    from app.logging_config import set_request_id
    
    set_request_id()
    
    response = create_error_response(
        code=error.code,
        message=str(error),  # Even if we pass exception string
        details=error.details,
    )
    
    # Convert to JSON string to check content
    import json
    response_str = json.dumps(response)
    
    # Should not contain Python exception patterns
    assert "Traceback" not in response_str
    assert "File \"" not in response_str
    assert "line " not in response_str
    assert "Exception:" not in response_str


# Additional test: Multiple requests get different correlation IDs
def test_unique_correlation_ids_per_request():
    """Verify that each request gets a unique correlation ID."""
    request_ids = set()
    
    # Make multiple requests
    for _ in range(10):
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        
        # Verify it's unique
        assert request_id not in request_ids, (
            f"Request ID {request_id} was reused"
        )
        request_ids.add(request_id)
    
    # Verify we got 10 unique IDs
    assert len(request_ids) == 10


# Additional test: Client-provided request IDs are preserved
@settings(max_examples=50)
@given(request_id=st.uuids())
def test_client_provided_request_id_preserved(request_id):
    """Verify that client-provided request IDs are preserved."""
    # Make request with X-Request-ID header
    response = client.get(
        "/",
        headers={"X-Request-ID": str(request_id)},
    )
    
    # Verify the same request ID is returned
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == str(request_id)
