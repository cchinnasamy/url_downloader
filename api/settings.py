import os

__DB_ENGINE__ = "postgresql+psycopg2"
__DB_USER__ = "postgres"
__DB_PASSWORD__ = ""
__DB_HOST__ = ""
__DB_PORT__ = "5432"
__DB_NAME__ = "postgres"
DB_Conn_Str = __DB_ENGINE__ + "://" + __DB_USER__ + ":" + __DB_PASSWORD__ + "@" + __DB_HOST__ + ":" + __DB_PORT__ + "/" + __DB_NAME__

storage_path = r'/home/files'

RABBITMQ_HOST = ""
RABBITMQ_USER = ""
RABBITMQ_PASS = ""
