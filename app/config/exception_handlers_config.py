from fastapi import FastAPI, Request

from app.utils.error_handlers import exception_handler


async def exception_handler_(request: Request, exc: Exception):
    return await exception_handler(request, exc)


def configure(app: FastAPI):
    app.exception_handler(Exception)(exception_handler_)

