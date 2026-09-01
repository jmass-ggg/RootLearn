"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from app.middleware import CorrelationIdMiddleware
from app.routes import diagnosis, graph, health, root_gap, sessions, teachback, tutor

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    configure_logging(settings.log_level)
    logger.info("application_startup", environment=settings.environment)
    yield
    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title="RootLearn API",
    description="AI-powered knowledge debugger",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Include routers
app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(sessions.router, prefix=settings.api_v1_prefix, tags=["sessions"])
app.include_router(graph.router, prefix=settings.api_v1_prefix, tags=["graph"])
app.include_router(diagnosis.router, prefix=settings.api_v1_prefix, tags=["diagnosis"])
app.include_router(root_gap.router, prefix=settings.api_v1_prefix, tags=["root-gap"])
app.include_router(tutor.router, prefix=settings.api_v1_prefix, tags=["tutor"])
app.include_router(teachback.router, prefix=settings.api_v1_prefix, tags=["teachback"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "RootLearn API",
        "version": "0.1.0",
        "status": "running",
    }
