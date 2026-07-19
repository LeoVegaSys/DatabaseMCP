import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

MAX_QUERY_ROWS = int(os.getenv("MAX_QUERY_ROWS", 1000))
MAX_QUERIES_PER_MINUTE = int(os.getenv("MAX_QUERIES_PER_MINUTE", 100))
SERVER_HOST=os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT=int(os.getenv("SERVER_PORT", 8080))

BLOCKED_KEYWORDS = [
    "delete",
    "drop",
    "truncate",
    "update",
    "insert",
    "alter",
    "create"
]
