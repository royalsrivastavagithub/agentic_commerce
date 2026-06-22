from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["healthcheck"])
async def health_check():
    return {"status": "ok"}
