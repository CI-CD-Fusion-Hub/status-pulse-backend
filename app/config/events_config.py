import asyncio
import hashlib

from sqlalchemy import create_engine, select, text

from app.config.config import Settings
from app.models.db_models import Base
from app.utils.database import SQLALCHEMY_DATABASE_URL, SessionLocal
from app.models import db_models as model
from app.utils.enums import AccessLevel, DatabaseSchemas

config = Settings().app


async def create_admin_user():
    session = SessionLocal()

    async with session:
        admin_user = await session.execute(select(model.Users)
                                           .where(model.Users.email == config.get("admin_email")))
        admin_user = admin_user.scalars().first()

        if not admin_user:
            hashed_password = hashlib.sha512(config.get("admin_pass").encode('utf-8')).hexdigest()
            new_admin = model.Users(
                first_name="Admin",
                last_name="User",
                email=config.get("admin_email"),
                password=hashed_password,
                status="active",
                access_level=AccessLevel.ADMIN.value
            )
            session.add(new_admin)
            await session.commit()

        await session.close()


async def create_schemas():
    async with SessionLocal() as session:
        for schema in DatabaseSchemas:
            create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema.value}"

            await session.execute(text(create_schema_sql))

        await session.commit()


async def startup_event():
    # Database setup
    await create_schemas()

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    await create_admin_user()


async def shutdown_event():
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)


def configure(app):
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
