from fastapi import APIRouter, Depends, Request

from app.schemas.auth_sch import RegisterUser, LoginUser
from app.schemas.response_sch import Response
from app.schemas.users_sch import UserResponse
from app.services.auth_srv import AuthService

router = APIRouter()


def create_auth_service():
    return AuthService()


@router.post("/login", tags=["auth"])
async def login_user(request: Request, credentials: LoginUser,
                     auth_service: AuthService = Depends(create_auth_service)) -> UserResponse:
    return await auth_service.login(request, credentials)


@router.post("/logout", tags=["auth"])
async def logout_user(request: Request, auth_service: AuthService = Depends(create_auth_service)) -> Response:
    return await auth_service.logout(request)


@router.post("/register", tags=["auth"])
async def register_user(request: Request, user_info: RegisterUser,
                        auth_service: AuthService = Depends(create_auth_service)) -> UserResponse:
    return await auth_service.register_user(user_info)
