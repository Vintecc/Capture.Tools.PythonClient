from enum import Enum

class DataOutput(Enum):
    JSON = 0
    CSV = 1

class DatabaseType(Enum):
    INFLUXDB = 0
    TIMESCALEDB = 1

class TimeOutput(Enum):
    HUMANREADABLE = 0 # 
    EPOCH = 1 # Unix Epoch (nanoseconds)

class AuthorizationMethod(Enum):
    NOT_SET = -1
    USERNAME_PASSWORD = 0
    API_TOKEN = 1
    