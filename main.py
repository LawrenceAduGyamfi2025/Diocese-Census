from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Census Data Management System for the Catholic Diocese, Ghana",
    version="1.0.0"
)

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
