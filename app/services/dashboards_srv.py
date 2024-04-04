import uuid
from typing import List

from fastapi import status, Request
from sqlalchemy.orm import Session

from app.daos.dashboards_dao import DashboardDAO, DashboardError
from app.exceptions.custom_http_expeption import CustomHTTPException
from app.models import db_models as model
from app.schemas.dashboards_sch import DashboardOut, DashboardEndpoint, CreateDashboard, UpdateDashboard, \
    DashboardEndpointCreate, DashboardEndpointLight, DashboardOutLight
from app.utils.chart_processor import ChartProcessor
from app.utils.enums import SessionAttributes, DashboardScopes, AccessLevel
from app.utils.logger import Logger
from app.utils.response import ok, error

LOGGER = Logger().start_logger()


class DashboardService:
    def __init__(self, db: Session):
        self.dashboards_dao = DashboardDAO(db)
        self.chart_processor = ChartProcessor(db)

    @classmethod
    def _have_public_access(cls, dashboard: model.Dashboards):
        return dashboard.scope == DashboardScopes.PUBLIC.value

    @classmethod
    def _validate_user_access(cls, request: Request, dashboard_id: int):
        user_dashboards = request.session.get(SessionAttributes.USER_DASHBOARDS.value)

        if dashboard_id not in user_dashboards:
            LOGGER.warning(f"User does not have access to dashboard with ID {dashboard_id}.")
            raise CustomHTTPException(detail=f"Dashboard with ID {dashboard_id} does not exist.",
                                      status_code=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def _is_admin(cls, request: Request):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)
        return False if user_access_level != AccessLevel.ADMIN.value else True

    async def _get_dashboard(self, dashboard_id: int):
        dashboard = await self.dashboards_dao.get_by_id(dashboard_id)

        if not dashboard:
            LOGGER.warning(f"Dashboard with ID {dashboard_id} not found.")
            raise CustomHTTPException(detail=f"Dashboard with ID {dashboard_id} does not exist.",
                                      status_code=status.HTTP_404_NOT_FOUND)
        return dashboard

    async def get_all(self, request: Request):
        user_dashboards = request.session.get(SessionAttributes.USER_DASHBOARDS.value)
        dashboards = await self.dashboards_dao.get_all_by_ids(user_dashboards)

        dashboards_endpoints = [
            DashboardOutLight(
                id=dashboard.id,
                uuid=dashboard.uuid,
                name=dashboard.name,
                description=dashboard.description,
                scope=dashboard.scope,
                endpoints=[DashboardEndpointLight(name=e.endpoint.name,
                                                  status=e.endpoint.status.status)
                           for e in dashboard.endpoints]
            )
            for dashboard in dashboards
        ]
        if not dashboards:
            LOGGER.info("No dashboards found in the database.")
            return ok(message="No dashboards found.", data=[])

        LOGGER.info("Successfully retrieved all dashboards.")
        return ok(message="Successfully provided all dashboards.",
                  data=dashboards_endpoints)

    async def get_by_id(self, request: Request, dashboard_id: int):
        self._validate_user_access(request, dashboard_id)
        dashboard = await self._get_dashboard(dashboard_id)

        dashboard_endpoints = DashboardOut.model_validate(dashboard.as_dict())
        dashboard_endpoints.endpoints = [DashboardEndpoint(
            id=e.endpoint.id,
            name=e.endpoint.name,
            url=e.endpoint.url,
            status=e.endpoint.status.status,
            unit=e.unit,
            type=e.type,
            duration=e.duration,
            x=e.x, y=e.y, w=e.w, h=e.h, i=e.i
        )
            for e in dashboard.endpoints]

        LOGGER.info(f"Successfully retrieved dashboard {dashboard_id}.")
        return ok(message="Successfully provided dashboard.",
                  data=dashboard_endpoints)

    async def get_by_uuid(self, request: Request, dashboard_uuid: str):
        dashboard = await self.dashboards_dao.get_by_uuid(dashboard_uuid)
        if not dashboard:
            return error(message="Dashboard not found", status_code=status.HTTP_400_BAD_REQUEST)

        if not self._have_public_access(dashboard):
            self._validate_user_access(request, dashboard.id)

        dashboard_endpoints = DashboardOut.model_validate(dashboard.as_dict())
        dashboard_endpoints.endpoints = [DashboardEndpoint(
            id=e.endpoint.id,
            name=e.endpoint.name,
            url=e.endpoint.url,
            status=e.endpoint.status.status,
            unit=e.unit,
            type=e.type,
            duration=e.duration,
            x=e.x, y=e.y, w=e.w, h=e.h, i=e.i,
        )
            for e in dashboard.endpoints]

        LOGGER.info(f"Successfully retrieved dashboard {dashboard_uuid}.")
        return ok(message="Successfully provided dashboard.",
                  data=dashboard_endpoints)

    async def create_dashboard(self, request: Request, dashboard_data: CreateDashboard):
        try:
            LOGGER.info("Creating dashboard.")
            user_id = request.session.get(SessionAttributes.USER_ID.value)
            dashboard_data.user_id = user_id
            dashboard_data.uuid = str(uuid.uuid4())
            dashboard = await self.dashboards_dao.create(dashboard_data)

            return ok(
                message="Successfully created dashboard.",
                data=DashboardOut.model_validate(dashboard.as_dict())
            )
        except DashboardError as e:
            LOGGER.error(f"DuplicateDashboardError in create dashboard: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def update_dashboard(self, request: Request, dashboard_id: int, dashboard_data: UpdateDashboard):
        self._validate_user_access(request, dashboard_id)
        dashboard = await self._get_dashboard(dashboard_id)

        data_to_update = dashboard_data.model_dump()
        data_to_update = {k: v for k, v in data_to_update.items() if v is not None and k != 'endpoints'}

        dashboard = await self.dashboards_dao.update(dashboard.id, data_to_update)

        dashboard_endpoints = DashboardOut.model_validate(dashboard.as_dict())
        dashboard_endpoints.endpoints = [DashboardEndpoint(
            id=e.endpoint.id,
            name=e.endpoint.name,
            url=e.endpoint.url,
            status=e.endpoint.status.status,
            unit=e.unit,
            type=e.type,
            duration=e.duration
        )
             for e in dashboard.endpoints]

        LOGGER.info(f"Successfully updated dashboard ID {dashboard_id}.")
        return ok(
            message="Successfully updated dashboard.",
            data=dashboard_endpoints
        )

    async def _upsert_endpoints_to_dashboard(self, request: Request, dashboard_id: int,
                                             endpoints_order: List[DashboardEndpoint]):
        user_endpoints = request.session.get(SessionAttributes.USER_ENDPOINTS_PERM.value)

        for endpoint in endpoints_order:
            if endpoint.id not in user_endpoints.keys() and not self._is_admin(request):
                raise CustomHTTPException(detail=f"Dashboard cannot be updated, because "
                                                 f"endpoint with id {endpoint.id} does not exist.",
                                          status_code=status.HTTP_404_NOT_FOUND)

        await self.dashboards_dao.delete_assigned_endpoints(dashboard_id)
        await self.dashboards_dao.update_endpoints_in_dashboard(dashboard_id, endpoints_order)
        LOGGER.info(f"Successfully added endpoints to dashboard ID {dashboard_id}.")

    async def delete_dashboard(self, request: Request, dashboard_id: int):
        self._validate_user_access(request, dashboard_id)
        dashboard = await self._get_dashboard(dashboard_id)

        await self.dashboards_dao.delete(dashboard.id)

        LOGGER.info(f"Dashboard with ID {dashboard_id} has been successfully deleted.")
        return ok(message="Dashboard has been successfully deleted.")

    async def update_endpoints_order(self, request: Request, dashboard_id: int,
                                     endpoints_order: List[DashboardEndpoint]):
        self._validate_user_access(request, dashboard_id)
        dashboard = await self._get_dashboard(dashboard_id)

        await self._upsert_endpoints_to_dashboard(request, dashboard.id, endpoints_order)
        LOGGER.info(f"Successfully updated endpoints to dashboard ID {dashboard_id}.")
        return ok(message="Dashboard order has been successfully updated.", data=endpoints_order)

    async def add_endpoints_to_dashboard(self, request: Request, dashboard_id: int,
                                         endpoints_data: DashboardEndpointCreate):
        try:
            self._validate_user_access(request, dashboard_id)
            dashboard = await self._get_dashboard(dashboard_id)

            await self.dashboards_dao.add_endpoint_to_dashboard(dashboard.id, endpoints_data)

            LOGGER.info(f"Successfully updated endpoints to dashboard ID {dashboard_id}.")
            return ok(message="Dashboard has been successfully updated.", data=endpoints_data)

        except DashboardError as e:
            LOGGER.error(f"DashboardError in create dashboard: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def update_endpoint_widget(self, request: Request, dashboard_id: int, endpoints_data: DashboardEndpoint):
        self._validate_user_access(request, dashboard_id)
        dashboard = await self._get_dashboard(dashboard_id)

        await self.dashboards_dao.update_endpoint_in_dashboard(dashboard.id, endpoints_data)

        LOGGER.info(f"Successfully updated endpoint in dashboard - {dashboard_id}.")
        return ok(message="Dashboard has been successfully updated.", data=endpoints_data)

    async def delete_endpoint_widget(self, request: Request, dashboard_id: int, widget_id: int):
        self._validate_user_access(request, dashboard_id)
        await self._get_dashboard(dashboard_id)
        await self.dashboards_dao.delete_assigned_widget(dashboard_id, widget_id)

        LOGGER.info(f"Successfully deleted endpoint in dashboard - {dashboard_id}.")
        return ok(message="Widget has been successfully delete.")
