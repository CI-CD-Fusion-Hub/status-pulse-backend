class CustomHTTPException(Exception):
    def __init__(self, detail: str, status_code: str):
        self.detail = detail
        self.status_code = status_code
