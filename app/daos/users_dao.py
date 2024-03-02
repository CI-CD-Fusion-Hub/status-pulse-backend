from typing import List

from psycopg2 import errorcodes
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.models import db_models as model
from app.schemas.auth_sch import RegisterUser
from app.utils import database
from app.utils.enums import AccessLevel, UserStatus


class DuplicateUserError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class UserDAO:
    def __init__(self):
        self.db = database.SessionLocal()

    async def get_all(self) -> List[model.Users]:
        """Fetch all users."""
        async with self.db:
            result = await self.db.execute(select(model.Users).order_by(model.Users.name))
            return result.scalars().all()

    async def get_by_id(self, user_id: int) -> model.Users:
        """Fetch a specific user by its ID."""
        async with self.db:
            result = await self.db.execute(select(model.Users).where(model.Users.id == user_id))
            return result.scalars().first()

    async def get_by_email(self, email: str) -> model.Users:
        """Fetch a specific user by its Email."""
        async with self.db:
            result = await self.db.execute(select(model.Users).where(model.Users.email == email))
            return result.scalars().first()

    async def get_detailed_user_info_by_email(self, email: str) -> model.Notifications:
        """Fetch a user with their endpoints access."""
        async with self.db:
            stmt = (
                select(model.Users)
                .options(
                    joinedload(model.Users.endpoints).joinedload(model.UserEndpoints.endpoint),
                    joinedload(model.Users.notifications),
                    joinedload(model.Users.dashboards)
                )
                .where(model.Users.email == email)
            )
            result = await self.db.execute(stmt)
            return result.scalars().first()

    async def create(self, user_data: RegisterUser) -> model.Users:
        """Create a new user."""
        user = model.Users(
            name=user_data.name,
            password=user_data.password,
            email=user_data.email,
            status=UserStatus.ACTIVE.value,
            access_level=AccessLevel.NORMAL.value,
        )
        try:
            async with self.db:
                self.db.add(user)
                await self.db.commit()
                return user
        except IntegrityError as e:
            # Check the specific PostgresSQL error code (pgcode)
            if e.orig.pgcode == errorcodes.UNIQUE_VIOLATION:  # PostgresSQL unique violation error code
                await self.db.rollback()
                raise DuplicateUserError("User with that email already exists.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e

    async def update(self, user_id: int, updated_data) -> model.Users:
        """Update an existing user."""
        async with self.db:
            await self.db.execute(update(model.Users).where(model.Users.id == user_id).values(**updated_data))
            await self.db.commit()

        return await self.get_by_id(user_id)

    async def delete(self, user_id: int):
        """Delete an user."""
        async with self.db:
            await self.db.execute(delete(model.Users).where(model.Users.id == user_id))
            await self.db.commit()
