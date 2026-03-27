from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import Dict, Any
import uvicorn
from loguru import logger

from .schemas import TriageRequest, TriageResponse
from .orchestrator import TriageOrchestrator
from .config import get_settings, Settings
from .database.database import DatabaseManager

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Triage Backend",
    description="FastAPI backend for healthcare triage using agent chain and Llama 3 7B",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global orchestrator
    try:
        logger.info("Starting Healthcare Triage Backend...")
        
        # Initialize orchestrator
        orchestrator = TriageOrchestrator()
        
        # Initialize database
        db_manager = DatabaseManager()
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Healthcare Triage Backend...")


def get_orchestrator() -> TriageOrchestrator:
    """Get the global orchestrator instance"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return orchestrator


@app.post("/triage", response_model=TriageResponse)
async def triage_endpoint(
    request: TriageRequest,
    orch: TriageOrchestrator = Depends(get_orchestrator),
    settings: Settings = Depends(get_settings)
):
    """
    Main triage endpoint that processes health complaints through agent chain
    
    - **query**: Free-text health complaint (English only, max 2000 chars)
    
    Returns structured triage response with symptoms, level, and recommendations.
    """
    try:
        # Validate query length
        if len(request.query) > settings.max_query_length:
            raise HTTPException(
                status_code=400,
                detail=f"Query too long (max {settings.max_query_length} characters)"
            )
        
        # Process triage request
        response = await orch.process_triage(request)
        return response
        
    except ValueError as e:
        # Input validation errors
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Triage endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check(orch: TriageOrchestrator = Depends(get_orchestrator)):
    """
    Health check endpoint that returns system status
    """
    try:
        health_status = orch.get_health_status()
        
        # Return appropriate HTTP status based on health
        if health_status["status"] == "healthy":
            return health_status
        elif health_status["status"] == "degraded":
            return JSONResponse(status_code=200, content=health_status)
        else:
            return JSONResponse(status_code=503, content=health_status)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/stats")
async def get_stats():
    """
    Get system statistics and metrics
    """
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_stats()
        
        return {
            "database": stats,
            "application": {
                "name": "Healthcare Triage Backend",
                "version": "1.0.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@app.get("/")
async def root():
    """
    Root endpoint with basic API information
    """
    return {
        "name": "Healthcare Triage Backend",
        "version": "1.0.0",
        "description": "FastAPI backend for healthcare triage using agent chain",
        "endpoints": {
            "triage": "/triage - Main triage endpoint",
            "health": "/health - System health check",
            "stats": "/stats - System statistics",
            "docs": "/docs - API documentation"
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # Run the application
    settings = get_settings()
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        "logs/triage_backend.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.log_level
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.log_level,
        colorize=True
    )
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
