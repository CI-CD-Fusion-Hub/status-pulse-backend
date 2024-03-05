from enum import Enum


class DatabaseSchemas(Enum):
    CONFIG_SCHEMA = 'config'
    LOG_SCHEMA = 'log'
    NOTIFICATION_SCHEMA = 'notification'


class AccessLevel(Enum):
    ADMIN = 'Admin'
    NORMAL = 'User'


class UserStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class EndpointStatus(Enum):
    MEASURING = 'measuring'
    UNHEALTHY = 'unhealthy'
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    NODATA = 'nodata'


class EndpointPermissions(Enum):
    VIEW = 'View'
    UPDATE = 'Update'


class DashboardScopes(Enum):
    PUBLIC = 'Public'
    PRIVATE = 'Private'


class DashboardChartTypes(Enum):
    UPTIME = 'Uptime'
    LINE_CHART = 'LineChart'


class DashboardChartUnits(Enum):
    HOURS = 'Hours'
    DAY = 'Days'


class AuthMethods(Enum):
    CAS = 'CAS'
    AAD = 'Azure AD'
    LOCAL = 'Local'


class SessionAttributes(Enum):
    OAUTH_STATE = 'oauth_state'
    AUTH_METHOD = 'auth_method'
    USER_ID = 'user_id'
    USER_NAME = 'user_name'
    USER_ACCESS_LEVEL = 'user_access_level'
    USER_INFO = 'user_info'
    USER_ENDPOINTS_PERM = 'user_endpoints_perm'
    USER_NOTIFICATIONS = 'user_notifications'
    USER_DASHBOARDS = 'user_dashboards'

