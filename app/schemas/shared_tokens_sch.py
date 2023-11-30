from typing import Optional

from pydantic import BaseModel


class CreateToken(BaseModel):
    user_id: int
    endpoint_id: int
    used: bool
    token: str


class CreateTokenBody(BaseModel):
    exp_time_minutes: Optional[int] = 5
