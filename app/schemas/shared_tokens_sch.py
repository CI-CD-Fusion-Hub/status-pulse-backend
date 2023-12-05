from datetime import datetime

from pydantic import BaseModel, field_validator

from app.utils.enums import EndpointPermissions


class CreateToken(BaseModel):
    user_id: int
    endpoint_id: int
    used: bool
    token: str


class CreateTokenBody(BaseModel):
    expiration: int
    permissions: str

    class Config:
        json_schema_extra = {
            "example": {
                "expiration": 1701772285,
                "permissions": "View"
            }
        }

    @field_validator("permissions")
    def check_order_status(cls, permissions):
        """Validates Permissions."""
        if permissions in (ep.value for ep in EndpointPermissions):
            return permissions
        raise ValueError(
            f"{permissions} is not a valid permissions for endpoint. Valid status are: "
            f"{', '.join(ep.value for ep in EndpointPermissions)}")
