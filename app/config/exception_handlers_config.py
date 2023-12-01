from fastapi import FastAPI, Request

from app.exceptions.custom_http_expeption import CustomHTTPException
from app.utils.error_handlers import exception_handler


async def exception_handler_(request: Request, exc: Exception):
    return await exception_handler(request, exc)


async def http_exception_handler_(request: Request, exc: CustomHTTPException):
    return await http_exception_handler(request, exc)


def configure(app: FastAPI):
    app.exception_handler(Exception)(exception_handler_)
    app.exception_handler(CustomHTTPException)(http_exception_handler_)


