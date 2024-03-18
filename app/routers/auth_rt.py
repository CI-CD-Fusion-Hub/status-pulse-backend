from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.schemas.auth_sch import RegisterUser, LoginUser
from app.schemas.response_sch import Response
from app.schemas.users_sch import UserResponse
from app.services.auth_srv import AuthService
from app.utils.database import get_db

router = APIRouter()


def create_auth_service(db: Session = Depends(get_db)):
    return AuthService(db)


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
