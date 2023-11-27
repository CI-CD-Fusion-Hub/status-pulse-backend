import hashlib

from fastapi import status as Status

from app.schemas.users_sch import UserBaseOut, UpdateUserProfile
from app.daos.users_dao import UserDAO
from app.utils.enums import SessionAttributes
from app.utils.logger import Logger
from app.utils.response import ok, error

LOGGER = Logger().start_logger()


class UserService:
    def __init__(self):
        self.user_dao = UserDAO()

    @classmethod
    async def get_user_info_from_request(cls, request):
        return ok(
            message="Successfully provided user details.",
            data=request.session.get(SessionAttributes.USER_INFO.value)
        )

    async def update_user(self, user_id: int, user_data: UpdateUserProfile):
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            LOGGER.warning(f"User with ID {user_id} does not exist.")
            return error(f"User with ID {user_id} does not exist.", status_code=Status.HTTP_400_BAD_REQUEST)

        if user_data.password:
            LOGGER.info("Updating password for user")
            user_data.password = hashlib.sha512(user_data.password.encode('utf-8')).hexdigest()

        data_to_update = user_data.model_dump()
        data_to_update = {k: v for k, v in data_to_update.items() if v is not None and k != "confirm_password"}

        user = await self.user_dao.update(user_id, data_to_update)

        LOGGER.info(f"Successfully updated user ID {user_id}.")
        return ok(message="Successfully updated user.", data=UserBaseOut.model_validate(user.as_dict()))

