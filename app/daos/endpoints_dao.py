from typing import List

from psycopg2 import errorcodes
from sqlalchemy import select, delete, update, text
from sqlalchemy.exc import IntegrityError

from app.models import db_models as model
from app.schemas.endpoints_sch import CreateEndpointInDb
from app.utils import database


class DuplicateEndpointError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class EndpointDAO:
    def __init__(self):
        self.db = database.SessionLocal()

    async def get_all(self) -> List[model.Endpoints]:
        """Fetch all endpoints."""
        async with self.db:
            result = await self.db.execute(select(model.Endpoints).order_by(model.Endpoints.created_at))
            return result.scalars().all()

    async def get_all_with_latest_log_status(self):
        """Fetch all endpoints with their latest log status."""
        async with self.db:
            try:
                # Fetch all endpoints
                result = await self.db.execute(select(model.Endpoints).order_by(model.Endpoints.created_at))
                endpoints = result.scalars().all()

                # Fetch the latest log status for each endpoint
                for endpoint in endpoints:
                    if endpoint.log_table:
                        log_table_name = f"log.{endpoint.log_table}"
                        latest_log_result = await self.db.execute(
                            select(text('status'))
                            .select_from(text(log_table_name))
                            .order_by(text('created_at DESC'))
                            .limit(1)
                        )
                        latest_log = latest_log_result.scalar()
                        endpoint.status = latest_log

                return endpoints
            except Exception as e:
                await self.db.rollback()
                raise e

    async def get_by_id(self, endpoint_id: int) -> model.Endpoints:
        """Fetch a specific endpoint by its ID."""
        async with self.db:
            result = await self.db.execute(select(model.Endpoints).where(model.Endpoints.id == endpoint_id))
            return result.scalars().first()

    async def get_by_id_with_latest_log_status(self, endpoint_id: int) -> model.Endpoints:
        """Fetch a specific endpoint by its ID."""
        async with self.db:
            result = await self.db.execute(select(model.Endpoints).where(model.Endpoints.id == endpoint_id))
            endpoint = result.scalars().first()

            if endpoint.log_table:
                log_table_name = f"log.{endpoint.log_table}"
                latest_log_result = await self.db.execute(
                    select(text('status'))
                    .select_from(text(log_table_name))
                    .order_by(text('created_at DESC'))
                    .limit(1)
                )
                latest_log = latest_log_result.scalar()
                endpoint.status = latest_log

            return endpoint
    async def update(self, endpoint_id: int, updated_data) -> model.Endpoints:
        """Update an existing endpoint."""
        async with self.db:
            await self.db.execute(update(model.Endpoints)
                                  .where(model.Endpoints.id == endpoint_id).values(**updated_data))
            await self.db.commit()

        return await self.get_by_id(endpoint_id)

    async def delete(self, endpoint_id: int):
        """Delete an endpoint."""
        async with self.db:
            await self.db.execute(delete(model.Endpoints).where(model.Endpoints.id == endpoint_id))
            await self.db.commit()

    async def create(self, db_data: CreateEndpointInDb) -> model.Endpoints:
        """Create a new endpoint."""
        endpoint = model.Endpoints(
            log_table=db_data.log_table,
            name=db_data.name,
            description=db_data.description,
            url=db_data.url,
            threshold=db_data.threshold,
            application_id=db_data.application_id,
            cron=db_data.cron,
            status_code=db_data.status_code,
            response=db_data.response,
            type=db_data.type
        )
        try:
            async with self.db:
                self.db.add(endpoint)
                await self.db.commit()
                return endpoint
        except IntegrityError as e:
            # Check the specific PostgresSQL error code (pgcode)
            if e.orig.pgcode == errorcodes.UNIQUE_VIOLATION:  # PostgresSQL unique violation error code
                await self.db.rollback()
                raise DuplicateEndpointError("Endpoint with that email already exists.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e
