import uuid
from datetime import timedelta, datetime

from fastapi import Request, status
from app.daos.endpoints_dao import EndpointDAO, DuplicateEndpointError
from app.daos.log_table_dao import LogTableDAO
from app.models.db_models import create_log_table
from app.schemas.endpoints_sch import BaseEndpointsOut, CreateEndpoint, CreateEndpointInDb, UpdateEndpoint, EndpointsOut
from app.utils.logger import Logger
from app.utils.response import ok, error

LOGGER = Logger().start_logger()


class EndpointService:
    def __init__(self):
        self.endpoint_dao = EndpointDAO()
        self.log_table_dao = LogTableDAO()

    @classmethod
    def generate_table_name(cls):
        uuid_str = str(uuid.uuid4()).replace('-', '_')
        table_name = 't' + uuid_str

        # Truncate to 63 characters if necessary
        table_name = table_name[:63]

        return table_name

    async def get_all(self, request: Request):
        endpoints = await self.endpoint_dao.get_all_with_latest_log_status()
        if not endpoints:
            LOGGER.info("No endpoints found in the database.")

        LOGGER.info(f"Retrieved {len(endpoints)} endpoints.")
        return ok(message="Successfully provided all endpoints.",
                  data=[BaseEndpointsOut.model_validate(endpoint.as_dict()) for endpoint in endpoints])

    async def get_by_id(self, request: Request, endpoint_id: int):
        endpoint = await self.endpoint_dao.get_by_id_with_latest_log_status(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            return error(message=f"Endpoint with ID {endpoint_id} does not exist.",
                         status_code=status.HTTP_404_NOT_FOUND)

        LOGGER.info(f"Successfully retrieved endpoint with ID {endpoint_id}.")
        return ok(message="Successfully provided endpoint.",
                  data=BaseEndpointsOut.model_validate(endpoint.as_dict()))

    async def get_status_graph_by_id(self, request, endpoint_id):
        endpoint = await self.endpoint_dao.get_by_id(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            return error(message=f"Endpoint with ID {endpoint_id} does not exist.",
                         status_code=status.HTTP_404_NOT_FOUND)

        endpoint_data = EndpointsOut.model_validate(endpoint.as_dict())

        if endpoint.log_table:
            log_records = await self.log_table_dao.select_all_from_log_table(endpoint.log_table)
            endpoint_data.logs = [record._asdict() for record in log_records]

        return ok(message="Successfully provided status graph for endpoint.",
                  data=endpoint_data.logs)

    async def get_uptime_graph_by_id(self, request: Request, endpoint_id: int):
        endpoint = await self.endpoint_dao.get_by_id(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            return error(message=f"Endpoint with ID {endpoint_id} does not exist.",
                         status_code=status.HTTP_404_NOT_FOUND)

        hourly_logs = []
        hours = 72

        if endpoint.log_table:
            logs = await self.log_table_dao.select_logs_from_last_hours(endpoint.log_table, hours)

            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)

            for hour in range(hours):
                current_hour_start = start_time + timedelta(hours=hour)
                next_hour_start = current_hour_start + timedelta(hours=1)

                # Ensure the next_hour_start does not exceed the end_time
                if next_hour_start > end_time:
                    next_hour_start = end_time

                logs_current_hour = [log._asdict() for log in logs
                                     if current_hour_start <= log._asdict()['created_at'] < next_hour_start]

                error_log = next((log for log in logs_current_hour if log['status'] != 'ok'), None)

                if error_log:
                    hourly_log = error_log
                elif logs_current_hour:
                    hourly_log = max(logs_current_hour, key=lambda log: log['created_at'])
                else:
                    hourly_log = {"hour": current_hour_start.strftime("%Y-%m-%d %H:%M:%S"), "status": "nodata",
                                  "details": "No logs for this hour"}

                hourly_logs.append(hourly_log)

            print(len(hourly_logs))
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
            await create_log_table(log_table)

            return ok(
                message="Successfully created endpoint.",
                data=BaseEndpointsOut.model_validate(endpoint.as_dict())
            )
        except DuplicateEndpointError as e:
            LOGGER.error(f"DuplicateEndpointError in create_endpoint: {e}")
            return error(message=e.detail, status_code=status.HTTP_400_BAD_REQUEST)

    async def update_endpoint(self, request: Request, endpoint_id: int, endpoint_data: UpdateEndpoint):
        endpoint = await self.endpoint_dao.get_by_id(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Endpoint with ID {endpoint_id} not found.")
            return error(message=f"Endpoint with ID {endpoint_id} does not exist.",
                         status_code=status.HTTP_404_NOT_FOUND)

        data_to_update = endpoint_data.model_dump()
        data_to_update = {k: v for k, v in data_to_update.items() if v is not None}

        endpoint = await self.endpoint_dao.update(endpoint_id, data_to_update)

        LOGGER.info(f"Successfully updated endpoint ID {endpoint_id}.")
        return ok(message="Successfully updated endpoint.", data=BaseEndpointsOut.model_validate(endpoint.as_dict()))

    async def delete_endpoint(self, request: Request, endpoint_id: int):
        endpoint = await self.endpoint_dao.get_by_id(endpoint_id)
        if not endpoint:
            LOGGER.warning(f"Attempted to delete a non-existent endpoint with ID {endpoint_id}.")
            return error(
                message=f"Endpoint with ID {endpoint_id} does not exist.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await self.endpoint_dao.delete(endpoint_id)
        await self.log_table_dao.delete_log_table(endpoint.log_table)
        LOGGER.info(f"Endpoint with ID {endpoint_id} has been successfully deleted.")
        return ok(message="Endpoint has been successfully deleted.")
