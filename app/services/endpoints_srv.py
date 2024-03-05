import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import Request, status

from app.daos.endpoints_dao import EndpointDAO, DuplicateEndpointError
from app.daos.log_table_dao import LogTableDAO
from app.daos.notification_table_dao import NotificationTableDAO
from app.daos.shared_tokens_dao import SharedTokenDAO
from app.exceptions.custom_http_expeption import CustomHTTPException
from app.models.db_models import create_log_table, create_notification_table
from app.schemas.endpoints_sch import BaseEndpointsOut, CreateEndpoint, CreateEndpointInDb, UpdateEndpoint, \
    EndpointsOut, EndpointLogs, EndpointNotificationLogs
from app.schemas.shared_tokens_sch import CreateToken, CreateTokenBody
from app.utils.chart_processor import ChartProcessor
from app.utils.enums import SessionAttributes, AccessLevel, EndpointStatus, EndpointPermissions, DashboardChartUnits, \
    DashboardChartTypes
from app.utils.logger import Logger
from app.utils.response import ok, error
from app.utils.token_manager import TokenManager

LOGGER = Logger().start_logger()


class EndpointService:
    def __init__(self):
        self.endpoint_dao = EndpointDAO()
        self.log_table_dao = LogTableDAO()
        self.chart_processor = ChartProcessor()
        self.notification_table_dao = NotificationTableDAO()
        self.shared_token_dao = SharedTokenDAO()

    @classmethod
    def generate_table_name(cls):
        uuid_str = str(uuid.uuid4()).replace('-', '_')
        table_name = 't' + uuid_str

        # Truncate to 63 characters if necessary
        table_name = table_name[:63]

        return table_name

    @classmethod
    def _validate_access(cls, request: Request, endpoint_id: int):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)
        user_endpoints_with_perm = request.session.get(SessionAttributes.USER_ENDPOINTS_PERM.value)

        if user_access_level != AccessLevel.ADMIN.value and endpoint_id not in user_endpoints_with_perm.keys():
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            raise CustomHTTPException(detail=f"Endpoint with ID {endpoint_id} does not exist.",
                                      status_code=status.HTTP_404_NOT_FOUND)

        LOGGER.info(f"User access validated for endpoint with ID {endpoint_id}.")

    @classmethod
    def _validate_user_rights(cls, request: Request, endpoint_id: int):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)
        user_endpoints_with_perm = request.session.get(SessionAttributes.USER_ENDPOINTS_PERM.value)

        if user_access_level != AccessLevel.ADMIN.value and \
                user_endpoints_with_perm[endpoint_id]["permissions"] != EndpointPermissions.UPDATE.value:
            LOGGER.warning(f"User does not have access to update/delete Endpoint with ID {endpoint_id}")
            raise CustomHTTPException(detail="You do not have permissions to perform this actions.",
                                      status_code=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def _is_admin(cls, request: Request):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)
        return False if user_access_level != AccessLevel.ADMIN.value else True

    async def _get_endpoint(self, endpoint_id: int):
        endpoint = await self.endpoint_dao.get_by_id(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            raise CustomHTTPException(detail=f"Endpoint with ID {endpoint_id} does not exist.",
                                      status_code=status.HTTP_404_NOT_FOUND)

        return endpoint

    async def fetch_endpoints(self, request: Request, page: int, per_page: int, search_query: str):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)

        if user_access_level != AccessLevel.ADMIN.value:
            LOGGER.info("Fetching endpoints based on user-specific access.")
            user_endpoints_perm = request.session.get(SessionAttributes.USER_ENDPOINTS_PERM.value)

            return await self.fetch_user_specific_endpoints(user_endpoints_perm, page, per_page, search_query)

        LOGGER.info("Fetching all endpoints for admin user.")
        return await self.fetch_admin_endpoints(page, per_page, search_query)

    async def fetch_user_specific_endpoints(self, user_endpoints_perm: dict, page: int, per_page: int,
                                            search_query: str):
        endpoints = await self.endpoint_dao.get_all_with_latest_log_status(page, per_page, search_query,
                                                                           user_endpoints_perm)
        total_count = await self.endpoint_dao.count_total_invoices(search_query, user_endpoints_perm)
        return endpoints, total_count

    async def fetch_admin_endpoints(self, page: int, per_page: int, search_query: str):
        endpoints = await self.endpoint_dao.get_all_with_latest_log_status(page, per_page, search_query, is_admin=True)
        total_count = await self.endpoint_dao.count_total_invoices(search_query=search_query)
        return endpoints, total_count

    async def get_all(self, request: Request, page: int = 1, per_page: int = 10, search_query: str = None):
        endpoints, total_count = await self.fetch_endpoints(request, page, per_page, search_query)

        if not endpoints:
            LOGGER.info("No endpoints found in the database.")
            return ok(message="No endpoints found.", data=[])

        endpoints_rsp = []
        for e in endpoints:
            endpoint_rsp = BaseEndpointsOut.model_validate(e.as_dict())

            endpoint_rsp.notifications = [{"id": n.notification.id, "name": n.notification.name}
                                          for n in e.notifications]
            endpoints_rsp.append(endpoint_rsp)

        LOGGER.info(f"Retrieved {len(endpoints)} endpoints.")
        return ok(
            message="Successfully provided all endpoints.",
            data={
                "data": [endpoint for endpoint in endpoints_rsp],
                "total_count": total_count,
                "pages": (total_count + per_page - 1) // per_page
            }
        )

    async def get_by_id(self, request: Request, endpoint_id: int):
        self._validate_access(request, endpoint_id)
        user_endpoints_with_perm = request.session.get(SessionAttributes.USER_ENDPOINTS_PERM.value)

        is_admin = self._is_admin(request)
        endpoint = await self.endpoint_dao.get_by_id_with_latest_log_status(endpoint_id, user_endpoints_with_perm,
                                                                            is_admin)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            return error(message=f"Endpoint with ID {endpoint_id} does not exist.",
                         status_code=status.HTTP_404_NOT_FOUND)
        endpoint_rsp = BaseEndpointsOut.model_validate(endpoint.as_dict())

        endpoint_rsp.notifications = [{"id": n.notification.id, "name": n.notification.name}
                                      for n in endpoint.notifications]
        LOGGER.info(f"Successfully retrieved endpoint with ID {endpoint_id}.")
        return ok(message="Successfully provided endpoint.",
                  data=endpoint_rsp)

    async def get_status_graph_by_id(self, request: Request, endpoint_id: int, duration: int = 24):
        self._validate_access(request, endpoint_id)
        endpoint = await self._get_endpoint(endpoint_id)

        if not endpoint.log_table:
            return ok(message="No logs found.", data=[])

        updated_logs = await self.chart_processor.process_line_chart(endpoint, DashboardChartUnits.HOURS.value, duration)

        return ok(message="Successfully provided status graph for endpoint.",
                  data=updated_logs)

    async def get_uptime_graph_by_id(self, request: Request, endpoint_id: int, duration: int = 72):
        self._validate_access(request, endpoint_id)
        endpoint = await self._get_endpoint(endpoint_id)
        if not endpoint.log_table:
            return ok(message="No logs found.", data=[])

        hourly_logs = await self.chart_processor.process_uptime_chart(endpoint,
                                                                      DashboardChartUnits.HOURS.value, duration)

        return ok(message="Successfully provided status graph for endpoint.",
                  data=hourly_logs)

    async def get_widget_graph_by_id(self, request: Request, endpoint_id: int, chart_type: str, unit: str, duration: int):
        self._validate_access(request, endpoint_id)
        endpoint = await self._get_endpoint(endpoint_id)
        if not endpoint.log_table:
            return ok(message="No logs found.", data=[])

        if unit not in (dcu.value for dcu in DashboardChartUnits):
            return error(message=f"{unit} is not a valid unit. Valid units are: "
                                 f"{', '.join(dcu.value for dcu in DashboardChartUnits)}")

        if chart_type not in (dct.value for dct in DashboardChartTypes):
            return error(message=f"{chart_type} is not a valid chart type. Valid types are: "
                                 f"{', '.join(dct.value for dct in DashboardChartTypes)}")

        if unit == DashboardChartUnits.DAY.value and (duration < 1 or duration > 31):
            return error(message=f"{duration} should be a valid number between 1 and 31 days.")
        if unit == DashboardChartUnits.HOURS.value and (duration < 1 or duration > 72):
            return error(message=f"{duration} should be a valid number between 1 and 72 hours.")

        logs = []
        if endpoint.log_table and chart_type == DashboardChartTypes.LINE_CHART.value:
            logs = await self.chart_processor.process_line_chart(endpoint, unit, duration)

        if endpoint.log_table and chart_type == DashboardChartTypes.UPTIME.value:
            logs = await self.chart_processor.process_uptime_chart(endpoint, unit, duration)

        return ok(message="Successfully provided widget.",
                  data=logs)

    async def create_endpoint(self, request: Request, endpoint_data: CreateEndpoint):
        try:
            LOGGER.info("Creating endpoint with local auth method.")
            log_table = self.generate_table_name()
            db_data = CreateEndpointInDb(
                name=endpoint_data.name,
                description=endpoint_data.description,
                url=endpoint_data.url,
                threshold=endpoint_data.threshold,
                application_id=endpoint_data.application_id,
                cron=endpoint_data.cron,
                status_code=endpoint_data.status_code,
                response=endpoint_data.response,
                type=endpoint_data.type,
                log_table=log_table)

            endpoint = await self.endpoint_dao.create(db_data)
            endpoint.status = None
            await self.endpoint_dao.assign_endpoint_to_user(endpoint.id,
                                                            request.session.get(SessionAttributes.USER_ID.value),
                                                            EndpointPermissions.UPDATE.value)
            await self.endpoint_dao.register_endpoint_status(endpoint.id, EndpointStatus.MEASURING.value)
            await create_log_table(log_table)
            await create_notification_table(log_table)

            if endpoint_data.notifications:
                await self._upsert_notifications_to_endpoint(request, endpoint.id, endpoint_data.notifications)

            endpoint_response = BaseEndpointsOut.model_validate(endpoint.as_dict())
            endpoint_response.status = EndpointStatus.MEASURING.value
            endpoint_response.notifications = endpoint_data.notifications
            return ok(
                message="Successfully created endpoint.",
                data=endpoint_response
            )
        except DuplicateEndpointError as e:
            LOGGER.error(f"DuplicateEndpointError in create_endpoint: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def update_endpoint(self, request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint):
        self._validate_access(request, endpoint_id)
        await self._get_endpoint(endpoint_id)
        self._validate_user_rights(request, endpoint_id)

        data_to_update = endpoint_data.model_dump()
        data_to_update = {k: v for k, v in data_to_update.items() if v is not None and k != 'notifications'}

        await self._upsert_notifications_to_endpoint(request, endpoint_id, endpoint_data.notifications)

        endpoint = await self.endpoint_dao.update(endpoint_id, data_to_update)

        endpoint_response = BaseEndpointsOut.model_validate(endpoint.as_dict())
        endpoint_response.notifications = endpoint_data.notifications

        LOGGER.info(f"Successfully updated endpoint ID {endpoint_id}.")
        return ok(message="Successfully updated endpoint.", data=endpoint_response)

    async def delete_endpoint(self, request: Request, endpoint_id: int):
        self._validate_access(request, endpoint_id)
        endpoint = await self._get_endpoint(endpoint_id)
        self._validate_user_rights(request, endpoint_id)

        await self.endpoint_dao.delete(endpoint_id)

        await self.log_table_dao.delete_log_table(endpoint.log_table)
        await self.notification_table_dao.delete_log_table(endpoint.log_table)

        LOGGER.info(f"Endpoint with ID {endpoint_id} has been successfully deleted.")
        return ok(message="Endpoint has been successfully deleted.")

    async def share_endpoint(self, request, endpoint_id: int, token_cfg: CreateTokenBody):
        self._validate_access(request, endpoint_id)
        await self._get_endpoint(endpoint_id)
        self._validate_user_rights(request, endpoint_id)

        token = TokenManager.generate_share_token(endpoint_id, token_cfg)
        await self.shared_token_dao.create(
            CreateToken(user_id=request.session.get(SessionAttributes.USER_ID.value),
                        token=token, endpoint_id=endpoint_id, used=False)
        )
        return ok(message="Share token is generated.", data=token)

    async def validate_shared_endpoint(self, request: Request, token: str):
        if not token:
            LOGGER.warning("No token provided.")
            return error(message="Token is required.", status_code=status.HTTP_404_NOT_FOUND)

        token_db = await self.shared_token_dao.get_by_token(token)
        if not token_db:
            LOGGER.warning("Token is not found in database.")
            return error(message="Invalid token",
                         status_code=status.HTTP_404_NOT_FOUND)

        if token_db.used:
            LOGGER.warning("Token has already been used")
            return error(message="Token has already been used.",
                         status_code=status.HTTP_404_NOT_FOUND)

        try:
            decoded_token = await TokenManager.validate_share_token(token)
            await self.endpoint_dao.assign_endpoint_to_user(decoded_token['endpoint_id'],
                                                            request.session.get(SessionAttributes.USER_ID.value),
                                                            decoded_token['permissions'])
            await self.shared_token_dao.update(token_db.id, {"used": True})

            return ok(message="Successfully added endpoint for user.")
        except ValueError as e:
            LOGGER.error(f"Token validation error: {e}")
            return error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
        except DuplicateEndpointError as e:
            LOGGER.error(f"DuplicateEndpointError in create_endpoint: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def get_uptime_logs_by_interval(self, request: Request, endpoint_id: int, date_from: datetime,
                                          date_to: datetime, full: bool):
        self._validate_access(request, endpoint_id)
        endpoint = await self._get_endpoint(endpoint_id)

        endpoint_data = EndpointsOut.model_validate(endpoint.as_dict())

        if endpoint.log_table:
            log_records = await self.log_table_dao.select_logs_by_interval(endpoint.log_table, date_from, date_to, full)
            updated_logs = [
                EndpointLogs(
                    id=log.id,
                    endpoint_id=log.endpoint_id,
                    response=log.response,
                    response_time=log.response_time,
                    status=log.status,
                    created_at=int(log.created_at.replace(tzinfo=timezone.utc).timestamp())
                ) for log in log_records
            ]

            endpoint_data.logs = [record for record in updated_logs]

        return ok(message="Successfully provided status graph for endpoint.",
                  data=endpoint_data.logs)

    async def _upsert_notifications_to_endpoint(self, request: Request, endpoint_id: int, notification_ids: List[int]):
        user_notifications_set = request.session.get(SessionAttributes.USER_NOTIFICATIONS.value)

        for notification_id in notification_ids:
            if notification_id not in user_notifications_set:
                raise CustomHTTPException(detail=f"Notification with id {notification_id} does not exist.",
                                          status_code=status.HTTP_404_NOT_FOUND)

        await self.endpoint_dao.delete_assigned_notifications(endpoint_id)
        await self.endpoint_dao.assign_notifications(endpoint_id, notification_ids)
        LOGGER.info(f"Successfully added notification to endpoint ID {endpoint_id}.")

    async def get_endpoint_notifications(self, request: Request, endpoint_id: int, hours: int = 72):
        self._validate_access(request, endpoint_id)
        endpoint = await self._get_endpoint(endpoint_id)

        if endpoint.log_table:
            log_records = await self.notification_table_dao.select_logs_from_last_hours(endpoint.log_table, hours)

            updated_logs = [
                EndpointNotificationLogs(
                    id=log.id, endpoint_id=log.endpoint_id, notification_id=log.notification_id,
                    notification_name=log.notification_name, notification_type=log.notification_type,
                    response=log.response, status=log.status,
                    created_at=int(log.created_at.replace(tzinfo=timezone.utc).timestamp())
                    ) for log in log_records
            ]

            return ok(message="Successfully provided status graph for endpoint.",
                      data=updated_logs)

        return ok(message="No logs found.",
                  data=[])
