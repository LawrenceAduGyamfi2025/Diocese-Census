from fastapi import FastAPI
from app.core.config import settings
from app.models.database import engine, Base
from app.api.auth import router as auth_router
from app.api.census import router as census_router
from app.api.analytics import router as analytics_router
from app.api.ai import router as ai_router

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Census Data Management System for the Catholic Diocese, Ghana",
    version="1.0.0"
)

# Include Routers
app.include_router(auth_router)
app.include_router(census_router)
app.include_router(analytics_router)
app.include_router(ai_router)

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for container orchestration and uptime monitoring.
    """
    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "database_configured": bool(settings.DB_URL)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
