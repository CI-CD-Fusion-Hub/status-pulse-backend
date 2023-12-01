from datetime import datetime

from pydantic import BaseModel


class CreateToken(BaseModel):
    user_id: int
    endpoint_id: int
    used: bool
    token: str


class CreateTokenBody(BaseModel):
    expiration: int
