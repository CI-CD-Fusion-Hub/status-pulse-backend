from typing import Optional

from pydantic import BaseModel


class CreateNotification(BaseModel):
    user_id: Optional[int] = None
    name: str
    description: str
    type: str
    properties: dict

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Name of the notification",
                "description": "Description of the notification",
                "type": "mattermost",
                "properties": {}
            }
        }


class UpdateNotification(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    properties: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Name of the notification",
                "description": "Description of the notification",
                "type": "mattermost",
                "properties": {}
            }
        }


# Response models
class NotificationOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    type: str
    properties: dict
    created_at: str



