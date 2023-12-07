from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.utils.enums import DashboardScopes


class CreateDashboard(BaseModel):
    user_id: Optional[int] = None
    uuid: Optional[str] = None
    name: str
    description: str
    scope: str
    endpoints: Optional[List[int]] = []

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
    endpoints: Optional[List[int]] = []

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


# Response models
class DashboardEndpoint(BaseModel):
    id: int
    url: str
    name: str
    status: str


class DashboardOut(BaseModel):
    id: int
    uuid: str
    name: str
    description: str
    scope: str
    endpoints: List[DashboardEndpoint] = []



