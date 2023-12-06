from typing import List, Dict

from psycopg2 import errorcodes
from sqlalchemy import select, delete, update, String, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from app.models import db_models as model
from app.schemas.endpoints_sch import CreateEndpointInDb
from app.utils import database
from app.utils.enums import EndpointPermissions


class DuplicateEndpointError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class EndpointDAO:
    def __init__(self):
        self.db = database.SessionLocal()

    async def get_all_with_latest_log_status(self, page: int, per_page: int, search_query: str,
                                             user_endpoints: dict = None,
                                             is_admin: bool = False) -> List[model.Endpoints]:
        """Fetch all endpoints with their latest log status."""
        async with self.db:
            try:
                endpoints = await self._fetch_endpoints_with_filter(page, per_page, search_query,
                                                                    user_endpoints, is_admin)

                self._apply_permissions(endpoints, user_endpoints)
                return endpoints
            except Exception as e:
                await self.db.rollback()
                raise e

    async def _fetch_endpoints_with_filter(self, page: int, per_page: int, search_query: str,
                                           user_endpoints: dict, is_admin: bool) -> List[model.Endpoints]:
        """Fetch endpoints based on given criteria."""
        query = select(model.Endpoints).options(
            selectinload(model.Endpoints.notifications).selectinload(model.EndpointNotifications.notification)
        ).join(model.EndpointsStatus)

        # Apply filtering for non-admin users
        if not is_admin:
            if user_endpoints:
                query = query.where(model.Endpoints.id.in_(user_endpoints.keys()))
            else:
                return []

        # Apply search filter
        if search_query:
            search_filter = or_(
                model.Endpoints.name.ilike(f"%{search_query}%"),
                model.Endpoints.description.ilike(f"%{search_query}%"),
                model.Endpoints.url.ilike(f"%{search_query}%"),
                model.Endpoints.response.cast(String).ilike(f"%{search_query}%"),
                model.EndpointsStatus.status.ilike(f"%{search_query}%")  # Ensure this relation exists and is correct
            )
            query = query.where(search_filter)

        # Apply ordering and pagination
        query = query.order_by(model.Endpoints.created_at).offset((page - 1) * per_page).limit(per_page)

        # Execute the query and fetch results
        result = await self.db.execute(query)
        return result.scalars().all()

    def _apply_permissions(self, endpoints: List[model.Endpoints], user_endpoints: Dict[int, dict] = None) -> None:
        """Apply permissions to endpoints."""
        for endpoint in endpoints:
            if user_endpoints and endpoint.id in user_endpoints:
                endpoint.permission = user_endpoints[endpoint.id]["permissions"]
            else:
                endpoint.permission = EndpointPermissions.UPDATE.value

    async def get_by_id(self, endpoint_id: int) -> model.Endpoints:
        """Fetch a specific endpoint by its ID."""
        async with self.db:
            result = await self.db.execute(select(model.Endpoints).where(model.Endpoints.id == endpoint_id))
            return result.scalars().first()

    async def get_by_id_with_latest_log_status(self, endpoint_id: int, user_endpoints: dict, is_admin: bool) \
            -> model.Endpoints:
        """Fetch a specific endpoint by its ID."""
        async with self.db:
            result = await self.db.execute(select(model.Endpoints)
                                           .options(joinedload(model.Endpoints.notifications)
                                                    .joinedload(model.EndpointNotifications.notification))
                                           .join(model.EndpointsStatus)
                                           .where(model.Endpoints.id == endpoint_id))
            endpoint = result.scalars().first()

            if not endpoint:
                return {}

            if is_admin:
                endpoint.permission = EndpointPermissions.UPDATE.value
                return endpoint

            endpoint.permission = user_endpoints[endpoint.id]["permissions"]
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

    async def assign_endpoint_to_user(self, endpoint_id: int, user_id: int, permissions: str):
        """Assign user to endpoint with specific permissions."""
        user_endpoint = model.UserEndpoints(
            user_id=user_id,
            endpoint_id=endpoint_id,
            permissions=permissions
        )
        try:
            async with self.db:
                self.db.add(user_endpoint)
                await self.db.commit()
                return user_endpoint
        except IntegrityError as e:
            # Check the specific PostgresSQL error code (pgcode)
            if e.orig.pgcode == errorcodes.UNIQUE_VIOLATION:  # PostgresSQL unique violation error code
                await self.db.rollback()
                raise DuplicateEndpointError("User already have access to this endpoint.")
            else:
                # Handle other types of IntegrityError (foreign key, etc.) as needed
                await self.db.rollback()
                raise e

    async def register_endpoint_status(self, endpoint_id: int, status: str | None):
        """Assign user to endpoint with specific permissions."""
        user_endpoint = model.EndpointsStatus(
            endpoint_id=endpoint_id,
            status=status
        )
        try:
            async with self.db:
                self.db.add(user_endpoint)
                await self.db.commit()
                return user_endpoint
        except IntegrityError as e:
            # Handle other types of IntegrityError (foreign key, etc.) as needed
            await self.db.rollback()
            raise e

    async def count_total_invoices(self, search_query: str = None, user_endpoints: dict = None):
        """Count the total number of endpoints in the database."""
        async with self.db:
            query = select(func.count()).select_from(model.Endpoints)
            if user_endpoints:
                query = query.where(model.Endpoints.id.in_(user_endpoints.keys()))

            if search_query:
                search_filter = or_(
                    model.Endpoints.name.ilike(f"%{search_query}%"),
                    model.Endpoints.description.ilike(f"%{search_query}%"),
                    model.Endpoints.url.ilike(f"%{search_query}%"),
                    model.Endpoints.response.cast(String).ilike(f"%{search_query}%"),
                    model.EndpointsStatus.status.ilike(f"%{search_query}%")
                )
                query = query.join(model.EndpointsStatus).where(search_filter)

            result = await self.db.execute(query)
            count = result.scalar()
            return count

    async def assign_notifications(self, endpoint_id: int, notification_ids: List[int]):
        """Add a list of notifications to a specific endpoint."""
        notifications = [model.EndpointNotifications(endpoint_id=endpoint_id, notification_id=notification_id)
                         for notification_id in notification_ids]

        async with self.db:
            self.db.add_all(notifications)
            await self.db.commit()

    async def delete_assigned_notifications(self, endpoint_id: int):
        """Delete a notifications for endpoint."""
        async with self.db:
            await self.db.execute(delete(model.EndpointNotifications)
                                  .where(model.EndpointNotifications.endpoint_id == endpoint_id))
            await self.db.commit()
