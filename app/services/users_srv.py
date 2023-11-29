import hashlib

from fastapi import status as Status, Request

from app.schemas.users_sch import UserBaseOut, UpdateUserProfile, UpdateUserAdmin
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

    async def get_all(self):
        users = await self.user_dao.get_all()
        LOGGER.info("Successfully retrieved all users.")

        return ok(message="Successfully provided all users.",
                  data=[UserBaseOut.model_validate(user.as_dict()) for user in users])

    async def get_by_id(self, request: Request, user_id: int):
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            LOGGER.warning(f"User with ID {user_id} does not exist.")
            return error(message=f"User with ID {user_id} does not exist.", status_code=Status.HTTP_404_NOT_FOUND)

        LOGGER.info(f"Successfully retrieved details for user ID {user_id}.")
        return ok(message="Successfully provided user details.", data=UserBaseOut.model_validate(user.as_dict()))

    async def update_user(self, user_id: int, user_data: UpdateUserProfile | UpdateUserAdmin):
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

    async def delete_user(self, user_id: int):
        if not await self.user_dao.get_by_id(user_id):
            LOGGER.warning(f"Attempted to delete a non-existent user with ID {user_id}.")
            return error(
                message=f"User with ID {user_id} does not exist.",
                status_code=Status.HTTP_404_NOT_FOUND
            )

        await self.user_dao.delete(user_id)
        LOGGER.info(f"User with ID {user_id} has been successfully deleted.")
        return ok(message="User has been successfully deleted.")

