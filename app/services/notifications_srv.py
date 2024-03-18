from fastapi import status, Request
from sqlalchemy.orm import Session

from app.daos.notifications_dao import NotificationDAO, DuplicateNotificationError
from app.exceptions.custom_http_expeption import CustomHTTPException
from app.schemas.notifications_sch import NotificationOut, CreateNotification, UpdateNotification
from app.utils.enums import SessionAttributes
from app.utils.logger import Logger
from app.utils.response import ok, error

LOGGER = Logger().start_logger()


class NotificationService:
    def __init__(self, db: Session):
        self.notification_dao = NotificationDAO(db)

    @classmethod
    def _validate_user_access(cls, request: Request, notification_id: int):
        user_notifications = request.session.get(SessionAttributes.USER_NOTIFICATIONS.value)

        if notification_id not in user_notifications:
            LOGGER.warning(f"User does not have access to notification with ID {notification_id}.")
            raise CustomHTTPException(detail=f"Notification with ID {notification_id} does not exist.",
                                      status_code=status.HTTP_400_BAD_REQUEST)

    async def _get_notification(self, notification_id: int):
        notification = await self.notification_dao.get_by_id(notification_id)
        if not notification:
            LOGGER.warning(f"Notification with ID {notification_id} not found.")
            raise CustomHTTPException(detail=f"Notification with ID {notification_id} does not exist.",
                                      status_code=status.HTTP_404_NOT_FOUND)

        return notification

    async def get_all(self, request: Request):
        user_notifications = request.session.get(SessionAttributes.USER_NOTIFICATIONS.value)
        notifications = await self.notification_dao.get_all_by_ids(user_notifications)

        if not notifications:
            LOGGER.info("No notifications found in the database.")
            return ok(message="No notifications found.", data=[])

        LOGGER.info("Successfully retrieved all notifications.")
        return ok(message="Successfully provided all notifications.",
                  data=[NotificationOut.model_validate(notification.as_dict()) for notification in notifications])

    async def get_by_id(self, request: Request, notification_id: int):
        self._validate_user_access(request, notification_id)
        notification = await self._get_notification(notification_id)

        LOGGER.info(f"Successfully retrieved notification with ID {notification_id}.")
        return ok(message="Successfully provided notification.",
                  data=NotificationOut.model_validate(notification.as_dict()))

    async def create_notification(self, request: Request, notification_data: CreateNotification):
        try:
            LOGGER.info("Creating notification.")
            user_id = request.session.get(SessionAttributes.USER_ID.value)
            notification_data.user_id = user_id
            notification = await self.notification_dao.create(notification_data)
            return ok(
                message="Successfully created notification.",
                data=NotificationOut.model_validate(notification.as_dict())
            )
        except DuplicateNotificationError as e:
            LOGGER.error(f"DuplicateNotificationError in create notification: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def update_notification(self, request: Request, notification_id: int, notification_data: UpdateNotification):
        self._validate_user_access(request, notification_id)
        notification = await self._get_notification(notification_id)

        data_to_update = notification_data.model_dump()
        data_to_update = {k: v for k, v in data_to_update.items() if v is not None}

        notification = await self.notification_dao.update(notification.id, data_to_update)

        LOGGER.info(f"Successfully updated notification ID {notification_id}.")
        return ok(
            message="Successfully updated notification.",
            data=NotificationOut.model_validate(notification.as_dict())
        )

    async def delete_notification(self, request: Request, notification_id: int):
        self._validate_user_access(request, notification_id)
        notification = await self._get_notification(notification_id)

        await self.notification_dao.delete(notification.id)

        LOGGER.info(f"Notification with ID {notification_id} has been successfully deleted.")
        return ok(message="Notification has been successfully deleted.")
