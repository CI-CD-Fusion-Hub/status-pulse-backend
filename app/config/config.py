from pydantic import Field
from pydantic_settings import BaseSettings

from typing import Dict


class Settings(BaseSettings):
    app_name: str = Field(..., env="app_name")
    app_version: str = Field(..., env="app_version")
    app_secret_key: str = Field(..., env="app_secret_key")
    app_root_path: str = Field(..., env="app_root_path")
    app_host: str = Field(..., env="app_host")
    app_port: int = Field(..., env="app_port")
    app_session_lifetime: int = Field(..., env="app_session_lifetime")
    app_disable_auth: bool = Field(..., env="app_disable_auth")
    app_env: str = Field(..., env="app_env")
    app_ssl_key: str = Field(..., env="app_ssl_key")
    app_ssl_cert: str = Field(..., env="app_ssl_cert")
    app_admin_email: str = Field(..., env="app_admin_email")
    app_admin_pass: str = Field(..., env="app_admin_pass")
    app_token_secret: str = Field(..., env="app_token_secret")
    app_workers: int = Field(..., env="app_workers")

    db_host: str = Field(..., env="db_host")
    db_user: str = Field(..., env="db_user")
    db_password: str = Field(..., env="db_password")
    db_name: str = Field(..., env="db_name")
    db_pool_size: str = Field(..., env="db_pool_size")
    db_max_overflow: str = Field(..., env="db_max_overflow")

    email_domain_name: str = Field(..., env="email_domain_name")
    email_host: str = Field(..., env="email_host")
    email_port: int = Field(..., env="email_port")
    email_username: str = Field(..., env="email_username")
    email_password: str = Field(..., env="email_password")

    @property
    def app(self) -> Dict[str, str]:
        return {
            "name": self.app_name,
            "version": self.app_version,
            "secret_key": self.app_secret_key,
            "root_path": self.app_root_path,
            "host": self.app_host,
            "port": int(self.app_port),
            "session_lifetime": self.app_session_lifetime,
            "disable_auth": self.app_disable_auth,
            "env": self.app_env,
            "ssl_cert": self.app_ssl_cert,
            "ssl_key": self.app_ssl_key,
            "admin_email": self.app_admin_email,
            "admin_pass": self.app_admin_pass,
            "workers": self.app_workers
        }

    @property
    def database(self) -> Dict[str, str]:
        return {
            "host": self.db_host,
            "user": self.db_user,
            "password": self.db_password,
            "name": self.db_name,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow
        }

    @property
    def token(self) -> Dict[str, str]:
        return {
            "secret": self.app_token_secret
        }

    @property
    def email(self) -> Dict[str, str]:
        return {
            "domain_name": self.email_domain_name,
            "host": self.email_host,
            "port": self.email_port,
            "username": self.email_username,
            "password": self.email_password
        }

    class Config:
        env_file = ".env"


