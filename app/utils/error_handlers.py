import traceback
from fastapi import Request

from app.utils.response import error


async def exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return error()
