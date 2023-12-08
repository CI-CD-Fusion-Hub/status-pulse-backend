from typing import List

from psycopg2 import errorcodes
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models import db_models as model
from app.schemas.dashboards_sch import CreateDashboard, DashboardEndpointCreate, DashboardEndpoint
from app.utils import database
from app.utils.logger import Logger

LOGGER = Logger().start_logger()


class DashboardError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class DashboardDAO:
    def __init__(self):
        self.db = database.SessionLocal()

    async def get_all(self) -> List[model.Dashboards]:
        """Fetch all dashboards."""
        async with self.db:
            result = await self.db.execute(select(model.Dashboards).order_by(model.Dashboards.created_at))
            return result.scalars().all()

    async def get_all_by_ids(self, ids: List[int]) -> List[model.Dashboards]:
        """Fetch all dashboards by ids."""
        async with self.db:
            result = await self.db.execute(select(model.Dashboards)
                                           .options(selectinload(model.Dashboards.endpoints)
                                                    .selectinload(model.DashboardEndpoints.endpoint))
                                           .where(model.Dashboards.id.in_(ids))
                                           .order_by(model.Dashboards.created_at))
            return result.scalars().all()

    async def get_by_id(self, dashboard_id: int) -> model.Dashboards:
        """Fetch a specific dashboard by ID."""
        async with self.db:
            result = await self.db.execute(
                select(model.Dashboards)
                .options(selectinload(model.Dashboards.endpoints)
                         .selectinload(model.DashboardEndpoints.endpoint))
                .where(model.Dashboards.id == dashboard_id)
            )

        return result.scalars().first()

    async def get_by_uuid(self, dashboard_uuid: str) -> model.Dashboards:
        """Fetch a specific dashboard by ID."""
        async with self.db:
            result = await self.db.execute(select(model.Dashboards)
                                           .options(selectinload(model.Dashboards.endpoints)
                                                    .selectinload(model.DashboardEndpoints.endpoint))
                                           .where(model.Dashboards.uuid == dashboard_uuid))
            return result.scalars().first()

    async def create(self, dashboard_data: CreateDashboard) -> model.Dashboards:
        """Create a new dashboard."""
        dashboard = model.Dashboards(
            uuid=dashboard_data.uuid,
            name=dashboard_data.name,
            description=dashboard_data.description,
            scope=dashboard_data.scope,
            user_id=dashboard_data.user_id,
        )
        try:
            async with self.db:
                self.db.add(dashboard)
                await self.db.commit()
                return dashboard
        except IntegrityError as e:
            if e.orig.pgcode == errorcodes.UNIQUE_VIOLATION:  # PostgresSQL unique violation error code
                await self.db.rollback()
                raise DashboardError("Dashboard with that name already exists for this user.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e

    async def update(self, dashboard_id: int, data_to_update: dict) -> model.Dashboards:
        """Update an existing dashboard."""
        async with self.db:
            await self.db.execute(update(model.Dashboards)
                                  .where(model.Dashboards.id == dashboard_id).values(**data_to_update))
            await self.db.commit()

        return await self.get_by_id(dashboard_id)

    async def delete(self, dashboard_id: int):
        """Delete a dashboard."""
        async with self.db:
            await self.db.execute(delete(model.Dashboards).where(model.Dashboards.id == dashboard_id))
            await self.db.commit()

    async def update_endpoints_in_dashboard(self, dashboard_id: int, endpoints_data: List[DashboardEndpoint]):
        """Add a list of endpoints to a specific dashboard."""
        try:
            endpoints = [
                model.DashboardEndpoints(
                    dashboard_id=dashboard_id,
                    endpoint_id=endpoint.id,
                    position=position,
                    type=endpoint.type,
                    unit=endpoint.unit,
                    duration=endpoint.duration
                )
                for position, endpoint in enumerate(endpoints_data)]
            async with self.db:
                self.db.add_all(endpoints)
                await self.db.commit()
        except IntegrityError as e:
            if e.orig.pgcode == errorcodes.FOREIGN_KEY_VIOLATION \
                    and 'is not present in table "endpoints"' in str(e.orig):
                await self.db.rollback()
                raise DashboardError("Dashboard have been created but some of the endpoints does not exist.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e

    async def delete_assigned_endpoints(self, dashboard_id: int) -> None:
        """Delete all endpoints for a dashboard."""
        async with self.db:
            await self.db.execute(delete(model.DashboardEndpoints)
                                  .where(model.DashboardEndpoints.dashboard_id == dashboard_id))
            await self.db.commit()

    async def add_endpoint_to_dashboard(self, dashboard_id: int, endpoints_data: DashboardEndpointCreate,
                                        first_available_position: int):
        """Add a new endpoints to a specific dashboard."""
        try:
            endpoints = [
                model.DashboardEndpoints(
                    dashboard_id=dashboard_id,
                    endpoint_id=endpoint_id,
                    position=position,
                    type=endpoints_data.type,
                    unit=endpoints_data.unit,
                    duration=endpoints_data.duration
                )
                for position, endpoint_id in enumerate(endpoints_data.endpoints, start=first_available_position)]

            async with self.db:
                self.db.add_all(endpoints)
                await self.db.commit()
        except IntegrityError as e:
            if e.orig.pgcode == errorcodes.FOREIGN_KEY_VIOLATION \
                    and 'is not present in table "endpoints"' in str(e.orig):
                await self.db.rollback()
                raise DashboardError("Dashboard have been created but some of the endpoints does not exist.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e

    async def get_next_position(self, dashboard_id: int) -> int:
        max_position_query = select(func.max(model.DashboardEndpoints.position)).where(
            model.DashboardEndpoints.dashboard_id == dashboard_id)

        async with self.db:
            result = await self.db.execute(max_position_query)
            max_position = result.scalar()

        return (max_position or 0) + 1
