from datetime import datetime, timedelta
from typing import Optional
from croniter import croniter, CroniterNotAlphaError, CroniterBadCronError

from pydantic import BaseModel, field_validator


class CreateEndpoint(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    threshold: int
    application_id: Optional[int] = None
    cron: str
    status_code: int
    response: Optional[dict] = {}
    type: str

    @field_validator('cron')
    def validate_cron_expression(cls, value):
        try:
            cron = croniter(value, datetime.now())

            next_run_1 = cron.get_next(datetime)
            next_run_2 = cron.get_next(datetime)

            if next_run_2 - next_run_1 < timedelta(minutes=1):
                raise ValueError("Cron schedule too frequent, should not be less than 1 minute apart")

            return value
        except (CroniterNotAlphaError, CroniterBadCronError):
            raise ValueError("Invalid cron syntax")


class UpdateEndpoint(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    threshold: Optional[int] = None
    application_id: Optional[int] = None
    cron: Optional[str] = None
    status_code: Optional[int] = None
    response: Optional[dict] = {}
    type: Optional[str] = None

    @field_validator('cron')
    def validate_cron_expression(cls, value):
        try:
            cron = croniter(value, datetime.now())

            next_run_1 = cron.get_next(datetime)
            next_run_2 = cron.get_next(datetime)

            if next_run_2 - next_run_1 < timedelta(minutes=1):
                raise ValueError("Cron schedule too frequent, should not be less than 1 minute apart")

            return value
        except (CroniterNotAlphaError, CroniterBadCronError):
            raise ValueError("Invalid cron syntax")


class CreateEndpointInDb(CreateEndpoint):
    log_table: str


# Response models
class BaseEndpointsOut(CreateEndpointInDb):
    id: int
    status: str | None


class EndpointsOut(BaseEndpointsOut):
    logs: Optional[list] = []



