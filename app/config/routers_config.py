from fastapi import FastAPI
from app.config.config import Settings

from app.routers import auth_rt, status_rt, users_rt, endpoints_rt, admin_rt, notifications_rt, dashboards_rt

config = Settings().app


def configure(app: FastAPI):
    app.include_router(auth_rt.router, prefix=config['root_path'])
    app.include_router(users_rt.router, prefix=config['root_path'])
    app.include_router(endpoints_rt.router, prefix=config['root_path'])
    app.include_router(status_rt.router, prefix=config['root_path'])
    app.include_router(admin_rt.router, prefix=config['root_path'])
    app.include_router(notifications_rt.router, prefix=config['root_path'])
    app.include_router(dashboards_rt.router, prefix=config['root_path'])


