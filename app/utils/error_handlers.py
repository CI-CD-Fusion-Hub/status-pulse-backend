import traceback
from fastapi import Request

from app.exceptions.custom_http_expeption import CustomHTTPException
from app.utils.response import error


async def exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return error()


async def http_exception_handler(request: Request, exc: CustomHTTPException):
    traceback.print_exc()
    return error(message=exc.detail, status_code=exc.status_code)
