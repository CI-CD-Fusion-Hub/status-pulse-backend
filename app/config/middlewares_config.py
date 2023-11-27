from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config.config import Settings

config = Settings().app


def configure(app: FastAPI):

    allow_origins = ["*"]
    same_site_value = "Strict"

    if config["env"] != 'prod':
        allow_origins = ["http://10.90.90.2:5173"]
        same_site_value = "None"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(SessionMiddleware,
                       secret_key=config['secret_key'],
                       https_only=True,
                       same_site=same_site_value,
                       max_age=int(config['session_lifetime']))
