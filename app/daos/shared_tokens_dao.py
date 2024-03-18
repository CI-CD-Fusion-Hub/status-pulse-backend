from typing import List

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import db_models as model
from app.schemas.shared_tokens_sch import CreateToken
from app.utils import database


class SharedTokenDAO:
    def __init__(self, db: Session = None):
        self.db = db or database.SessionLocal()

    async def get_all(self) -> List[model.ShareTokens]:
        """Fetch all tokens."""
        async with self.db:
            result = await self.db.execute(select(model.ShareTokens).order_by(model.ShareTokens.created_ts))
            return result.scalars().all()

    async def get_by_id(self, token_id: int) -> model.ShareTokens:
        """Fetch a specific token by its ID."""
        async with self.db:
            result = await self.db.execute(select(model.ShareTokens).where(model.ShareTokens.id == token_id))
            return result.scalars().first()

    async def get_by_token(self, token: str) -> model.ShareTokens:
        """Fetch a specific token by its name."""
        async with self.db:
            result = await self.db.execute(select(model.ShareTokens).where(model.ShareTokens.token == token))
            return result.scalars().first()

    async def create(self, token_data: CreateToken) -> model.ShareTokens:
        """Create a new token."""
        token = model.ShareTokens(
            user_id=token_data.user_id,
            endpoint_id=token_data.endpoint_id,
            used=token_data.used,
            token=token_data.token
        )
        try:
            async with self.db:
                self.db.add(token)
                await self.db.commit()
                return token
        except IntegrityError as e:
            # Handle other types of IntegrityError (foreign key, etc.) as needed
            await self.db.rollback()
            raise e

    async def update(self, token_id: int, updated_data) -> model.ShareTokens:
        """Update an existing token."""
        async with self.db:
            await self.db.execute(update(model.ShareTokens)
                                  .where(model.ShareTokens.id == token_id).values(**updated_data))
            await self.db.commit()

        return await self.get_by_id(token_id)

