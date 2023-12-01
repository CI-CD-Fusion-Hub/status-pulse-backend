from datetime import datetime

import jwt

from app.config.config import Settings
from app.utils.logger import Logger

token_config = Settings().token
LOGGER = Logger().start_logger()


class TokenManager:
    @staticmethod
    def generate_share_token(endpoint_id: int, timestamp: int):
        secret_key = token_config['secret']
        expiration_time = datetime.fromtimestamp(timestamp)

        token = jwt.encode(
            {
                'exp': expiration_time,
                'endpoint_id': endpoint_id
            },
            secret_key, algorithm='HS256')

        return token.decode('utf-8') if isinstance(token, bytes) else token

    @staticmethod
    async def validate_share_token(token: str) -> dict:
        secret_key = token_config['secret']
        try:
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_time = datetime.now()
            if datetime.utcfromtimestamp(decoded_token['exp']) < current_time:
                raise jwt.ExpiredSignatureError

            return decoded_token
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired.")
        except jwt.InvalidTokenError as e:
            LOGGER.warning(f"Invalid token: {e}")
            raise ValueError("Invalid token.")
