from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.schemas.users_sch import UserResponse, UpdateUserProfile
from app.services.users_srv import UserService
from app.utils.check_session import auth_required
from app.utils.database import get_db
from app.utils.enums import SessionAttributes

router = APIRouter()


def create_user_service(db: Session = Depends(get_db)):
    return UserService(db)


@router.get("/user", tags=["users"])
@auth_required
async def get_user_by_id(request: Request,
                         user_service: UserService = Depends(create_user_service)) -> UserResponse:
    return await user_service.get_user_info_from_request(request)


@router.put("/user/profile", tags=["users"])
@auth_required
async def update_user_profile(request: Request, user_data: UpdateUserProfile,
                              user_service: UserService = Depends(create_user_service)) -> UserResponse:
    user_id = request.session.get(SessionAttributes.USER_ID.value)
    return await user_service.update_user(user_id, user_data)
