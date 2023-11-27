import hashlib
from fastapi import Request
from fastapi import status as Status

from app.daos.users_dao import UserDAO, DuplicateUserError
from app.schemas.auth_sch import LoginUser, RegisterUser
from app.schemas.users_sch import UserBaseOut, CreateUserDB
from app.utils.enums import UserStatus, SessionAttributes, AccessLevel
from app.utils.response import ok, error
from app.utils.logger import Logger

LOGGER = Logger().start_logger()


class AuthService:
    def __init__(self):
        self.user_dao = UserDAO()

    @classmethod
    def _verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return hashlib.sha512(plain_password.encode('utf-8')).hexdigest() == hashed_password

    @classmethod
    async def logout(cls, request):
        LOGGER.info(f"User {request.session.get(SessionAttributes.USER_NAME.value)} successfully logged out.")
        request.session.clear()
        return ok(message="Successful logout.")

    async def register_user(self, user_info: RegisterUser):
        try:
            LOGGER.info("Creating user with local auth method")
            user_data = CreateUserDB(
                first_name=user_info.first_name,
                last_name=user_info.last_name,
                password=hashlib.sha512(user_info.password.encode('utf-8')).hexdigest(),
                email=user_info.email,
                status=UserStatus.ACTIVE.value,
                access_level=AccessLevel.NORMAL.value,
                )

            user = await self.user_dao.create(user_data)
            return ok(
                message="Successfully created user.",
                data=UserBaseOut.model_validate(user.as_dict())
            )

        except DuplicateUserError as e:
            LOGGER.error(f"DuplicateUserError in register_user: {e}")
            return error(message=e.detail, status_code=Status.HTTP_400_BAD_REQUEST)

    async def login(self, request: Request, credentials: LoginUser):
        user = await self.user_dao.get_by_email(credentials.email)
        if not user:
            LOGGER.warning(f"User with Email {credentials.email} does not exist.")
            return error(
                message=f"User with Email {credentials.email} does not exist.",
                status_code=Status.HTTP_404_NOT_FOUND
            )

        if user.status != UserStatus.ACTIVE.value:
            LOGGER.warning(f"User with Email {credentials.email} is inactive.")
            return error(
                message=f"User with Email {credentials.email} is inactive.",
                status_code=Status.HTTP_400_BAD_REQUEST
            )

        if not self._verify_password(credentials.password, user.password):
            LOGGER.warning("Invalid password or email.")
            return error(
                message="Invalid password or email.",
                status_code=Status.HTTP_400_BAD_REQUEST
            )

        request.session[SessionAttributes.USER_NAME.value] = credentials.email

        LOGGER.info(f"User {credentials.email} successfully logged in.")
        return ok(message="Successfully logged in.", data=UserBaseOut.model_validate(user.as_dict()))
