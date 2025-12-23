#!/usr/bin/env python3
"""FastAPI application for AIlice platform."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.database import init_db
from api.rate_limiter import RateLimitMiddleware
from api.routers import (
    auth,
    applications,
    scraping,
    social,
    cloud,
    ai_models,
    admin,
    billing,
    items,
    media,
    analytics,
    notifications,
    search,
    ai_inference,
    collaboration,
    system,
    files,
    integrations
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Initializing AIlice Platform API...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AIlice Platform API...")


# Create FastAPI app
app = FastAPI(
    title="AIlice Platform API",
    description="Enhanced AIlice platform with Pro tier capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
# Core functionality
app.include_router(auth.router)
app.include_router(applications.router)

# Content and data management
app.include_router(items.router)
app.include_router(media.router)
app.include_router(files.router)

# AI and integrations
app.include_router(ai_models.router)
app.include_router(ai_inference.router)
app.include_router(scraping.router)
app.include_router(social.router)
app.include_router(cloud.router)
app.include_router(integrations.router)

# Analytics and monitoring
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(search.router)

# Collaboration
app.include_router(collaboration.router)

# Billing and payments
app.include_router(billing.router)

# System and admin
app.include_router(system.router)
app.include_router(admin.router)


# Mount static files
import os as os_path
if os_path.exists('/home/ubuntu/viralspark_ailice/static'):
    app.mount("/static", StaticFiles(directory="/home/ubuntu/viralspark_ailice/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to admin dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIlice Platform</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }
            h1 { color: #333; }
            .links { margin-top: 30px; }
            .links a {
                display: block;
                margin: 10px 0;
                padding: 10px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
            .links a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🤖 AIlice Platform API</h1>
        <p>Welcome to the enhanced AIlice platform with Pro tier capabilities!</p>
        
        <div class="links">
            <a href="/docs">📚 API Documentation (Swagger UI)</a>
            <a href="/redoc">📖 API Documentation (ReDoc)</a>
            <a href="/admin/dashboard">⚙️ Admin Dashboard</a>
        </div>
    </body>
    </html>
    """


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve admin dashboard."""
    try:
        with open('/home/ubuntu/viralspark_ailice/static/admin_dashboard.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Admin Dashboard Not Found</h1>
            <p>The admin dashboard file could not be found.</p>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """



@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ailice-platform-api",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting AIlice Platform API on {host}:{port}")
    
    uvicorn.run(
        "fastapi_app:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        log_level="info"
    )