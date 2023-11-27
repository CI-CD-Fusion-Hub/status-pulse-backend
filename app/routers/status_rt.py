from fastapi import APIRouter

from app.schemas.response_sch import Response
from app.utils.response import ok

router = APIRouter()


@router.get("/status", tags=["status"])
async def status() -> Response:
    return ok(message="Service is healthy!")
