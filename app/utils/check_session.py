from functools import wraps

from starlette.requests import Request
from app.config.config import Settings
from app.daos.users_dao import UserDAO
from app.utils.enums import UserStatus, SessionAttributes, AccessLevel
from app.utils.logger import Logger
from app.utils.response import unauthorized, forbidden

LOGGER = Logger().start_logger()
config = Settings()


def auth_required(function_to_protect):
    @wraps(function_to_protect)
    async def wrapper(request: Request, *args, **kwargs):
        email = request.session.get(SessionAttributes.USER_NAME.value)
        if not email:
            return unauthorized()

        user_dao = UserDAO()
        user = await user_dao.get_detailed_user_info_by_email(email)

        if not user:
            return unauthorized()

        if user.status != UserStatus.ACTIVE.value:
            return unauthorized()

        endpoints_perm = {endpoint.endpoint.id: {"permissions": endpoint.permissions}
                          for endpoint in user.endpoints if endpoint.endpoint}
        notifications = [notification.id for notification in user.notifications]

        request.session[SessionAttributes.USER_INFO.value] = user.as_dict()
        request.session[SessionAttributes.USER_ACCESS_LEVEL.value] = user.access_level
        request.session[SessionAttributes.USER_ID.value] = user.id
        request.session[SessionAttributes.USER_ENDPOINTS_PERM.value] = endpoints_perm
        request.session[SessionAttributes.USER_NOTIFICATIONS.value] = notifications
        return await function_to_protect(request, *args, **kwargs)

    return wrapper


def admin_access_required(function_to_protect):
    @wraps(function_to_protect)
    async def wrapper(request: Request, *args, **kwargs):
        if request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value) == AccessLevel.ADMIN.value:
            return await function_to_protect(request, *args, **kwargs)

        return forbidden()

    return wrapper

