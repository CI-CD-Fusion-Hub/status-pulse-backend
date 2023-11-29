import re
from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.schemas.response_sch import Response
from app.utils.enums import AccessLevel, UserStatus


class ValidatorUtils:
    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        The regular expression pattern \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b matches any email address.
        The \b word boundary anchor ensures that the pattern matches only complete words. The [A-Za-z0-9._%+-]+ character
        class matches one or more occurrences of any alphanumeric character, dot, underscore, percent sign, plus sign or
        hyphen. The @[A-Za-z0-9.-]+ matches the at symbol and one or more occurrences of any alphanumeric character,
        dot or hyphen. The \.[A-Z|a-z]{2,} matches a dot followed by two or more occurrences of any uppercase or lowercase
        letter.
        """
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(regex, email):
            raise ValueError(
                f"Invalid email address {repr(email)}. Please, try again with different email.")
        return email

    @classmethod
    def validate_status(cls, status: str) -> str:
        """Validates that status is 'active' or 'inactive'."""
        if status in (us.value for us in UserStatus):
            return status
        raise ValueError(
            f"Invalid status {status}. Please, provide valid status {', '.join(us.value for us in UserStatus)}.")

    @classmethod
    def validate_access_level(cls, access_level: str) -> str:
        """Validates that access level is 'Admin' or 'User'."""
        if access_level in (al.value for al in AccessLevel):
            return access_level
        raise ValueError(
            f"{access_level} is not a valid access level. Valid types are: {', '.join(al.value for al in AccessLevel)}")

    @classmethod
    def validate_password(cls, password: str, info: ValidationInfo) -> str:
        """Validates that password and confirm_password match."""
        if password and 'confirm_password' not in info.data or info.data['confirm_password'] is None:
            raise ValueError("password and confirm_password do not match")

        if 'confirm_password' in info.data and info.data['confirm_password'] is not None:
            if password is None:
                raise ValueError("confirm_password must be set if password is set")
            if password != info.data['confirm_password']:
                raise ValueError("password and confirm_password do not match")
        return password


class UpdateUserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    confirm_password: Optional[str] = None
    password: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "asd",
                "last_name": "CH",
                "email": "test1@gmail.com",
                "password": "asdf@asdf",
                "confirm_password": "asdf@asdf",
            }
        }

    @field_validator("email")
    def email_check(cls, email):
        return ValidatorUtils.validate_email(email)

    @field_validator("password")
    def password_match(cls, password, info: ValidationInfo):
        return ValidatorUtils.validate_password(password, info)


class UserBaseOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    status: str
    created_at: str
    access_level: str


class CreateUserDB(BaseModel):
    first_name: str
    last_name: str
    password: str
    email: str
    status: str
    access_level: str


# Response models
class UserResponse(Response):
    data: UserBaseOut
