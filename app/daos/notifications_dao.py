from typing import List

from psycopg2 import errorcodes
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.notifications_sch import CreateNotification
from app.utils import database
from app.utils.logger import Logger
from app.models import db_models as model

LOGGER = Logger().start_logger()


class DuplicateNotificationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class NotificationDAO:
    def __init__(self, db: Session = None):
        self.db = db or database.SessionLocal()

    async def get_all(self) -> List[model.Notifications]:
        """Fetch all notifications."""
        async with self.db:
            result = await self.db.execute(select(model.Notifications).order_by(model.Notifications.created_at))
            return result.scalars().all()

    async def get_all_by_ids(self, ids: List[int]) -> List[model.Notifications]:
        async with self.db:
            result = await self.db.execute(select(model.Notifications).where(model.Notifications.id.in_(ids))
                                           .order_by(model.Notifications.created_at))
            return result.scalars().all()

    async def get_by_id(self, notification_id: int) -> model.Notifications:
        """Fetch a specific notification by ID."""
        async with self.db:
            result = await self.db.execute(select(model.Notifications).where(model.Notifications.id == notification_id))
            return result.scalars().first()

    async def create(self, notification_data: CreateNotification) -> model.Notifications:
        """Create a new notification."""
        notification = model.Notifications(
            name=notification_data.name,
            description=notification_data.description,
            type=notification_data.type,
            user_id=notification_data.user_id,
            properties=notification_data.properties
        )
        try:
            async with self.db:
                self.db.add(notification)
                await self.db.commit()
                return notification
        except IntegrityError as e:
            if e.orig.pgcode == errorcodes.UNIQUE_VIOLATION:  # PostgresSQL unique violation error code
                await self.db.rollback()
                raise DuplicateNotificationError("Notification with that name already exists for this user.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e

    async def update(self, notification_id: int, data_to_update: dict) -> model.Notifications:
        """Update an existing notification."""
        async with self.db:
            await self.db.execute(update(model.Notifications)
                                  .where(model.Notifications.id == notification_id).values(**data_to_update))
            await self.db.commit()

        return await self.get_by_id(notification_id)

    async def delete(self, notification_id: int):
        """Delete an notification."""
        async with self.db:
            await self.db.execute(delete(model.Notifications).where(model.Notifications.id == notification_id))
            await self.db.commit()


