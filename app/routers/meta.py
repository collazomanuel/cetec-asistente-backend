from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz", tags=["Meta"])
async def health_check():
    """Liveness probe"""
    return {"status": "ok"}

@router.get("/readyz", tags=["Meta"])
async def readiness_check():
    """Readiness probe"""
    return {"status": "ready"}
