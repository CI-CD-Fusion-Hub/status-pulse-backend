from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import FieldValidationInfo

from app.schemas.users_sch import ValidatorUtils


class RegisterUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    confirm_password: str
    password: str

    @field_validator("email", check_fields=True)
    def email_check(cls, email):
        return ValidatorUtils.validate_email(email)

    @field_validator("password", check_fields=True)
    def passwords_match(cls, password, info: FieldValidationInfo):
        return ValidatorUtils.validate_password(password, info)


class LoginUser(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def email_check(cls, email):
        return ValidatorUtils.validate_email(email)

