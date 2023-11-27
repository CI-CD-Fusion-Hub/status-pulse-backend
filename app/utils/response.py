from fastapi import status as Status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.utils.logger import Logger

LOGGER = Logger().start_logger()


def ok(status="success", message="", data=None):
    """HTTP Response 200"""
    return custom_response({
        "status": status,
        "message": message,
        "data": data
    }, Status.HTTP_200_OK)


def unauthorized():
    LOGGER.warning("Attempt to access resource without authorization")
    """HTTP Response 401"""
    return custom_response({
        "status": "error",
        "message": "Unauthorized",
        "data": None
    }, Status.HTTP_401_UNAUTHORIZED)


def forbidden():
    LOGGER.warning("Attempt to access resource without authorization")
    """HTTP Response 403"""
    return custom_response({
        "status": "error",
        "message": "Forbidden",
        "data": None
    }, Status.HTTP_403_FORBIDDEN)


def error(status="error", message="Oops!!! Something went wrong. Contact your support for more information.",
          data=None, status_code=Status.HTTP_500_INTERNAL_SERVER_ERROR):
    """HTTP Response 500"""
    if data:
        LOGGER.error(f"{message} Following exception occurred: {str(data)}")
    else:
        LOGGER.error(f"{message}")
                     
    return custom_response({
        "status": status,
        "message": message,
        "data": data
    }, status_code)


def custom_response(resp, status_code):
    return JSONResponse(status_code=status_code, content=jsonable_encoder(resp))

