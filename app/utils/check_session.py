from functools import wraps

from starlette.requests import Request
from app.config.config import Settings
from app.daos.users_dao import UserDAO
from app.utils.enums import UserStatus, SessionAttributes
from app.utils.logger import Logger
from app.utils.response import unauthorized

LOGGER = Logger().start_logger()
config = Settings()


def auth_required(function_to_protect):
    @wraps(function_to_protect)
    async def wrapper(request: Request, *args, **kwargs):
        email = request.session.get(SessionAttributes.USER_NAME.value)
        if not email:
            return unauthorized()

        user_dao = UserDAO()
        user = await user_dao.get_by_email(email)
        if not user:
            return unauthorized()

        if user.status != UserStatus.ACTIVE.value:
            return unauthorized()

        request.session[SessionAttributes.USER_INFO.value] = user.as_dict()
        request.session[SessionAttributes.USER_ACCESS_LEVEL.value] = user.access_level
        request.session[SessionAttributes.USER_ID.value] = user.id
        return await function_to_protect(request, *args, **kwargs)

    return wrapper

