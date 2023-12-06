import re
from datetime import datetime, timedelta

from sqlalchemy import text

from app.utils import database
from app.utils.enums import DatabaseSchemas
from app.utils.logger import Logger

LOGGER = Logger().start_logger()


class NotificationTableDAO:
    def __init__(self):
        self.db = database.SessionLocal()

    @classmethod
    def _sanitize_table_name(cls, table_name):
        """Sanitize the table name to prevent SQL injection."""
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise ValueError("Invalid table name")
        return table_name

    async def delete_log_table(self, table_name: str):
        """Delete a log table from the notification schema."""
        sanitized_table_name = self._sanitize_table_name(table_name)
        drop_table_sql = f"DROP TABLE IF EXISTS {DatabaseSchemas.NOTIFICATION_SCHEMA.value}.{sanitized_table_name};"

        async with self.db:
            try:
                await self.db.execute(text(drop_table_sql))
                await self.db.commit()
            except Exception as e:
                await self.db.rollback()
                raise e

    async def select_logs_from_last_hours(self, table_name: str, hours: int):
        """Select records from a specific log table for the last 24 hours."""
        sanitized_table_name = self._sanitize_table_name(table_name)
        twenty_four_hours_ago = datetime.now() - timedelta(hours=hours)
        # Format the timestamp in a way that's compatible with your database
        formatted_timestamp = twenty_four_hours_ago.strftime("%Y-%m-%d %H:%M:%S")

        select_query = (
            f"SELECT nt.*, n.name as notification_name, n.type as notification_type "
            f"FROM {DatabaseSchemas.NOTIFICATION_SCHEMA.value}.{sanitized_table_name} nt "
            f"JOIN {DatabaseSchemas.CONFIG_SCHEMA.value}.notifications n ON nt.notification_id = n.id "
            f"WHERE nt.created_at >= '{formatted_timestamp}' ORDER BY nt.created_at DESC;"
        )

        async with self.db:
            try:
                result = await self.db.execute(text(select_query))
                records = result.fetchall()
                return records
            except Exception as e:
                await self.db.rollback()
                raise e
