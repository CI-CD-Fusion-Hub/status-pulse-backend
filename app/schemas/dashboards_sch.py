from typing import Optional, List

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.utils.enums import DashboardScopes, DashboardChartTypes, DashboardChartUnits


class CreateDashboard(BaseModel):
    user_id: Optional[int] = None
    uuid: Optional[str] = None
    name: str
    description: str
    scope: str

    @field_validator("scope")
    def check_order_status(cls, scope):
        """Validates Scope."""
        if scope in (ds.value for ds in DashboardScopes):
            return scope
        raise ValueError(
            f"{scope} is not a valid scope for dashboard. Valid scopes are: "
            f"{', '.join(ds.value for ds in DashboardScopes)}")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Name of the dashboard",
                "description": "Description of the dashboard",
                "scope": "Public",
                "endpoints": [1, 2, 3]
            }
        }


class UpdateDashboard(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[str] = None

    @field_validator("scope")
    def check_order_status(cls, scope):
        """Validates Scope."""
        if scope in (ds.value for ds in DashboardScopes):
            return scope
        raise ValueError(
            f"{scope} is not a valid scope for dashboard. Valid scopes are: "
            f"{', '.join(ds.value for ds in DashboardScopes)}")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Name of the dashboard",
                "description": "Description of the dashboard",
                "scope": "Private",
                "endpoints": [1, 2, 3]
            }
        }


class DashboardEndpointCreate(BaseModel):
    endpoints: List[int]
    unit: str
    type: str
    duration: int

    @field_validator("type")
    def check_type(cls, type):
        """Validates Type."""
        if type in (det.value for det in DashboardChartTypes):
            return type
        raise ValueError(
            f"{type} is not a valid type for dashboard view. Valid type are: "
            f"{', '.join(ds.value for ds in DashboardChartTypes)}")

    @field_validator("duration")
    def check_duration(cls, duration, fields: ValidationInfo):
        """Validates Unit."""
        if fields.data['unit'] not in (dcu.value for dcu in DashboardChartUnits):
            raise ValueError(
                f"{fields.data['unit']} is not a valid type for dashboard view. Valid type are: "
                f"{', '.join(dcu.value for dcu in DashboardChartUnits)}")
        if fields.data['unit'] == DashboardChartUnits.DAY.value and (duration < 1 or duration > 90):
            raise ValueError(f"{duration} should be a valid number between 1 and 90 days.")
        if fields.data['unit'] == DashboardChartUnits.HOURS.value and (duration < 1 or duration > 72):
            raise ValueError(f"{duration} should be a valid number between 1 and 72 hours.")
        return duration


class DashboardEndpoint(BaseModel):
    id: int
    url: str
    name: str
    status: str
    unit: str
    type: str
    duration: int
    logs: Optional[list] = []

    class Config:
        json_schema_extra = {
            "example": {
                "endpoints": [
                    {
                        "id": 1,
                        "url": "https://testurl.com",
                        "name": "Test Url 1",
                        "status": "healthy"
                    },
                    {
                        "id": 2,
                        "url": "https://testurl2.com",
                        "name": "Test Url 2",
                        "status": "healthy"
                    },
                    {
                        "id": 3,
                        "url": "https://testurl3.com",
                        "name": "Test Url 3",
                        "status": "healthy"
                    }
                ]
            }
        }

    @field_validator("type")
    def check_type(cls, type):
        """Validates Type."""
        if type in (det.value for det in DashboardChartTypes):
            return type
        raise ValueError(
            f"{type} is not a valid type for dashboard view. Valid type are: "
            f"{', '.join(ds.value for ds in DashboardChartTypes)}")

    @field_validator("duration")
    def check_duration(cls, duration, fields: ValidationInfo):
        """Validates Unit."""
        if fields.data['unit'] not in (dcu.value for dcu in DashboardChartUnits):
            raise ValueError(
                f"{fields.data['unit']} is not a valid type for dashboard view. Valid type are: "
                f"{', '.join(dcu.value for dcu in DashboardChartUnits)}")
        if fields.data['unit'] == DashboardChartUnits.DAY.value and (duration < 1 or duration > 90):
            raise ValueError(f"{duration} should be a valid number between 1 and 90 days.")
        if fields.data['unit'] == DashboardChartUnits.HOURS.value and (duration < 1 or duration > 72):
            raise ValueError(f"{duration} should be a valid number between 1 and 72 hours.")
        return duration


# Response models
class DashboardOut(BaseModel):
    id: int
    uuid: str
    name: str
    description: str
    scope: str
    endpoints: List[DashboardEndpoint] = []



