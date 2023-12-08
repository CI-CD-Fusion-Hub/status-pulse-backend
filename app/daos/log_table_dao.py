import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import text, select, and_

from app.utils import database
from app.utils.enums import DatabaseSchemas, DashboardChartUnits
from app.utils.logger import Logger

LOGGER = Logger().start_logger()


class LogTableDAO:
    def __init__(self):
        self.db = database.SessionLocal()

    @classmethod
    def _sanitize_table_name(cls, table_name):
        """Sanitize the table name to prevent SQL injection."""
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise ValueError("Invalid table name")
        return table_name

    async def delete_log_table(self, table_name: str):
        """Delete a log table from the log schema."""
        sanitized_table_name = self._sanitize_table_name(table_name)
        drop_table_sql = f"DROP TABLE IF EXISTS {DatabaseSchemas.LOG_SCHEMA.value}.{sanitized_table_name};"

        async with self.db:
            try:
                await self.db.execute(text(drop_table_sql))
                await self.db.commit()
            except Exception as e:
                await self.db.rollback()
                raise e

    async def select_all_from_log_table(self, table_name: str):
        """Select all records from a specific log table."""
        sanitized_table_name = self._sanitize_table_name(table_name)
        select_query = f"SELECT * FROM {DatabaseSchemas.LOG_SCHEMA.value}.{sanitized_table_name} " \
                       f"ORDER BY created_at ASC;"

        async with self.db:
            try:
                result = await self.db.execute(text(select_query))
                records = result.fetchall()
                return records
            except Exception as e:
                await self.db.rollback()
                raise e

    async def select_logs_from_last_hours(self, table_name: str, unit: str, duration: int):
        """Select records from a specific log table for the last 24 hours."""
        sanitized_table_name = self._sanitize_table_name(table_name)
        if unit == DashboardChartUnits.HOURS.value:
            delta = datetime.now() - timedelta(hours=duration)
        elif unit == DashboardChartUnits.DAY.value:
            delta = datetime.now() - timedelta(days=duration)
        else:
            return []
        # Format the timestamp in a way that's compatible with your database
        formatted_timestamp = delta.strftime("%Y-%m-%d %H:%M:%S")

        select_query = (
            f"SELECT * FROM {DatabaseSchemas.LOG_SCHEMA.value}.{sanitized_table_name} "
            f"WHERE created_at >= '{formatted_timestamp}' ORDER BY created_at ASC;"
        )

        async with self.db:
            try:
                result = await self.db.execute(text(select_query))
                records = result.fetchall()
                return records
            except Exception as e:
                await self.db.rollback()
                raise e

    async def select_logs_by_interval(self, table_name: str, date_from: datetime = None,
                                      date_to: datetime = None, full: bool = False):
        """Select logs from a specified log table within a given time interval."""
        sanitized_table_name = self._sanitize_table_name(table_name)

        query = select("*").select_from(
            text(f"{DatabaseSchemas.LOG_SCHEMA.value}.{sanitized_table_name}")
        ).order_by(text('created_at DESC'))

        conditions = []
        params = {}

        if date_from:
            utc_date_from = date_from.astimezone(timezone.utc).replace(tzinfo=None)
            conditions.append(text("created_at >= :date_from"))
            LOGGER.debug(f"Get logs from date: {utc_date_from}")
            params['date_from'] = utc_date_from
        if date_to:
            utc_date_to = date_to.astimezone(timezone.utc).replace(tzinfo=None)
            conditions.append(text("created_at <= :date_to"))
            LOGGER.debug(f"Get logs to date: {utc_date_to}")
            params['date_to'] = utc_date_to

        if not full:
            conditions.append(text("status != 'healthy'"))

        if conditions:
            query = query.where(and_(*conditions))

        async with self.db:
            try:
                result = await self.db.execute(query, params)
                records = result.fetchall()
                return records
            except Exception as e:
                await self.db.rollback()
                raise e
