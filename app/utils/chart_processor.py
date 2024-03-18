from datetime import timezone, datetime, timedelta

from sqlalchemy.orm import Session

from app.daos.log_table_dao import LogTableDAO
from app.schemas.endpoints_sch import EndpointLogs, BaseEndpointLogs
from app.utils.enums import EndpointStatus, DashboardChartUnits
from app.models import db_models as model


class ChartProcessor:
    def __init__(self, db: Session):
        self.log_table_dao = LogTableDAO(db)

    async def process_line_chart(self, endpoint: model.Endpoints, unit: str, duration: int):
        log_records = await self.log_table_dao.select_logs_from_last_hours(endpoint.log_table, unit, duration)
        return [
            EndpointLogs(
                id=log.id,
                endpoint_id=log.endpoint_id,
                response=log.response,
                response_time=log.response_time,
                status=log.status,
                created_at=int(log.created_at.replace(tzinfo=timezone.utc).timestamp())
            ) for log in log_records
        ]

    async def process_uptime_chart(self, endpoint: model.Endpoints, unit: str, duration: int):
        hourly_logs = []
        logs = await self.log_table_dao.select_logs_from_last_hours(endpoint.log_table, unit, duration)

        current_time = datetime.now()
        if unit == DashboardChartUnits.HOURS.value:
            rounded_time = current_time + timedelta(hours=1)
            end_time = rounded_time.replace(minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)
            start_time = end_time - timedelta(hours=duration)
        else:
            rounded_time = current_time + timedelta(days=1)
            end_time = rounded_time.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)
            start_time = end_time - timedelta(days=duration)

        for d in range(duration):
            if unit == DashboardChartUnits.HOURS.value:
                current_hour_start = start_time + timedelta(hours=d)
                next_hour_start = current_hour_start + timedelta(hours=1)
            else:
                current_hour_start = start_time + timedelta(days=d)
                next_hour_start = current_hour_start + timedelta(days=1)

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
        return hourly_logs
