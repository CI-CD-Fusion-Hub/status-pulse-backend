import uuid
from datetime import timedelta, datetime, timezone

from fastapi import Request, status

from app.daos.endpoints_dao import EndpointDAO, DuplicateEndpointError
from app.daos.log_table_dao import LogTableDAO
from app.daos.shared_tokens_dao import SharedTokenDAO
from app.exceptions.custom_http_expeption import CustomHTTPException
from app.models.db_models import create_log_table
from app.schemas.endpoints_sch import BaseEndpointsOut, CreateEndpoint, CreateEndpointInDb, UpdateEndpoint, \
    EndpointsOut, EndpointLogs, BaseEndpointLogs
from app.schemas.shared_tokens_sch import CreateToken
from app.utils.enums import SessionAttributes, AccessLevel, EndpointStatus
from app.utils.logger import Logger
from app.utils.response import ok, error
from app.utils.token_manager import TokenManager

LOGGER = Logger().start_logger()


class EndpointService:
    def __init__(self):
        self.endpoint_dao = EndpointDAO()
        self.log_table_dao = LogTableDAO()
        self.shared_token_dao = SharedTokenDAO()

    @classmethod
    def generate_table_name(cls):
        uuid_str = str(uuid.uuid4()).replace('-', '_')
        table_name = 't' + uuid_str

        # Truncate to 63 characters if necessary
        table_name = table_name[:63]

        return table_name

    @classmethod
    async def _validate_user_access(cls, request: Request, endpoint_id: int):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)
        user_endpoints = request.session.get(SessionAttributes.USER_ENDPOINTS.value)

        if user_access_level != AccessLevel.ADMIN.value and endpoint_id not in user_endpoints:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            raise CustomHTTPException(detail=f"Endpoint with ID {endpoint_id} does not exist.",
                                      status_code=status.HTTP_404_NOT_FOUND)

        LOGGER.info(f"User access validated for endpoint with ID {endpoint_id}.")

    async def is_endpoint_exist(self, endpoint_id: int):
        endpoint = await self.endpoint_dao.get_by_id(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            raise CustomHTTPException(detail=f"Endpoint with ID {endpoint_id} does not exist.",
                                      status_code=status.HTTP_404_NOT_FOUND)

        return endpoint

    async def get_all(self, request: Request):
        user_access_level = request.session.get(SessionAttributes.USER_ACCESS_LEVEL.value)

        if user_access_level != AccessLevel.ADMIN.value:
            LOGGER.info("Fetching endpoints based on user-specific access.")
            user_endpoints = request.session.get(SessionAttributes.USER_ENDPOINTS.value)
            endpoints = await self.endpoint_dao.get_all_with_latest_log_status(user_endpoints)
        else:
            LOGGER.info("Fetching all endpoints for admin user.")
            endpoints = await self.endpoint_dao.get_all_with_latest_log_status()

        if not endpoints:
            LOGGER.info("No endpoints found in the database.")
            return ok(message="No endpoints found.", data=[])

        LOGGER.info(f"Retrieved {len(endpoints)} endpoints.")
        return ok(message="Successfully provided all endpoints.",
                  data=[BaseEndpointsOut.model_validate(endpoint.as_dict()) for endpoint in endpoints])

    async def get_by_id(self, request: Request, endpoint_id: int):
        await self._validate_user_access(request, endpoint_id)
        endpoint = await self.endpoint_dao.get_by_id_with_latest_log_status(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            return error(message=f"Endpoint with ID {endpoint_id} does not exist.",
                         status_code=status.HTTP_404_NOT_FOUND)

        LOGGER.info(f"Successfully retrieved endpoint with ID {endpoint_id}.")
        return ok(message="Successfully provided endpoint.",
                  data=BaseEndpointsOut.model_validate(endpoint.as_dict()))

    async def get_status_graph_by_id(self, request: Request, endpoint_id: int, hours: int = 24):
        await self._validate_user_access(request, endpoint_id)
        endpoint = await self.is_endpoint_exist(endpoint_id)

        endpoint_data = EndpointsOut.model_validate(endpoint.as_dict())

        if endpoint.log_table:
            log_records = await self.log_table_dao.select_logs_from_last_hours(endpoint.log_table, hours)
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

    async def get_uptime_graph_by_id(self, request: Request, endpoint_id: int, hours: int = 72):
        await self._validate_user_access(request, endpoint_id)
        endpoint = await self.is_endpoint_exist(endpoint_id)

        hourly_logs = []

        if endpoint.log_table:
            logs = await self.log_table_dao.select_logs_from_last_hours(endpoint.log_table, hours)

            current_time = datetime.now()
            rounded_time = current_time + timedelta(hours=1)
            end_time = rounded_time.replace(minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)
            start_time = end_time - timedelta(hours=hours)

            for hour in range(hours):
                current_hour_start = start_time + timedelta(hours=hour)
                next_hour_start = current_hour_start + timedelta(hours=1)

                # Ensure the next_hour_start does not exceed the end_time
                if next_hour_start > end_time:
                    next_hour_start = end_time

                logs_current_hour = [log._asdict() for log in logs
                                     if current_hour_start <= log._asdict()['created_at'] < next_hour_start]

                error_log = [log for log in logs_current_hour if log['status'] != 'healthy']

                if len(error_log) >= 3:
                    hourly_log = BaseEndpointLogs(
                        created_at=int(max(error_log, key=lambda log: log['created_at'])['created_at']
                                       .replace(tzinfo=timezone.utc).timestamp()),
                        status=EndpointStatus.DEGRADED.value)
                elif 3 > len(error_log) > 0:
                    hourly_log = BaseEndpointLogs(
                        created_at=int(max(error_log, key=lambda log: log['created_at'])['created_at']
                                       .replace(tzinfo=timezone.utc).timestamp()),
                        status=EndpointStatus.UNHEALTHY.value)
                elif logs_current_hour:
                    hourly_log = BaseEndpointLogs(
                        created_at=int(max(logs_current_hour, key=lambda log: log['created_at'])['created_at']
                                       .replace(tzinfo=timezone.utc).timestamp()),
                        status=EndpointStatus.HEALTHY.value)
                else:
                    hourly_log = BaseEndpointLogs(
                        created_at=int(current_hour_start.replace(tzinfo=timezone.utc).timestamp()),
                        status=EndpointStatus.NODATA.value)

                hourly_logs.append(hourly_log)

        return ok(message="Successfully provided status graph for endpoint.",
                  data=hourly_logs)

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
            await self.endpoint_dao.assign_endpoint_to_user(endpoint.id,
                                                            request.session.get(SessionAttributes.USER_ID.value))
            await create_log_table(log_table)

            return ok(
                message="Successfully created endpoint.",
                data=BaseEndpointsOut.model_validate(endpoint.as_dict())
            )
        except DuplicateEndpointError as e:
            LOGGER.error(f"DuplicateEndpointError in create_endpoint: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def update_endpoint(self, request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint):
        await self._validate_user_access(request, endpoint_id)
        await self.is_endpoint_exist(endpoint_id)

        data_to_update = endpoint_data.model_dump()
        data_to_update = {k: v for k, v in data_to_update.items() if v is not None}

        endpoint = await self.endpoint_dao.update(endpoint_id, data_to_update)

        LOGGER.info(f"Successfully updated endpoint ID {endpoint_id}.")
        return ok(message="Successfully updated endpoint.", data=BaseEndpointsOut.model_validate(endpoint.as_dict()))

    async def delete_endpoint(self, request: Request, endpoint_id: int):
        await self._validate_user_access(request, endpoint_id)
        endpoint = await self.is_endpoint_exist(endpoint_id)

        await self.endpoint_dao.delete(endpoint_id)

        await self.log_table_dao.delete_log_table(endpoint.log_table)
        LOGGER.info(f"Endpoint with ID {endpoint_id} has been successfully deleted.")
        return ok(message="Endpoint has been successfully deleted.")

    async def share_endpoint(self, request, endpoint_id: int, expiration: int):
        await self._validate_user_access(request, endpoint_id)
        await self.is_endpoint_exist(endpoint_id)

        token = TokenManager.generate_share_token(endpoint_id, expiration)
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
                                                            request.session.get(SessionAttributes.USER_ID.value))
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
        await self._validate_user_access(request, endpoint_id)
        endpoint = await self.is_endpoint_exist(endpoint_id)

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
