from db import get_connection, fetch_procedure_metadata, load_procedure_metadata
from ratelimiter import check_rate_limit
from config import DB_CONFIG
from logger import logger
from intelligence_engine import build_procedure_metadata


def register_discovery_tools(mcp):

    @mcp.tool()
    def list_databases():
        """List all databases in MySQL server"""

        check_rate_limit()

        conn = None

        try:
            conn = get_connection()
            cursor = conn.cursor()

            exclude_databases = {"mysql", "sys", "information_schema", "performance_schema"}
            cursor.execute("SHOW DATABASES")

            databases = [
                row[0] for row in cursor.fetchall()
                if row[0] not in exclude_databases
            ]

            return databases

        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            raise

        finally:
            if conn:
                conn.close()


    @mcp.tool()
    def list_tables(database_name: str = "mcp_demo"):
        """
        List all tables in a database.
        If database_name is not provided, default database from config is used.
        """

        check_rate_limit()

        conn = None

        try:

            conn = get_connection()
            cursor = conn.cursor()

            # Use default DB if not provided
            if not database_name:
                database_name = DB_CONFIG["database"]

            cursor.execute("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA=%s
                AND TABLE_TYPE='BASE TABLE'
            """, (database_name,))

            tables = [row[0] for row in cursor.fetchall()]

            return tables

        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            raise

        finally:
            if conn:
                conn.close()
                
    @mcp.tool()
    def describe_table(table_name: str, database_name: str = "mcp_demo"):
        """Describe structure of a table"""

        check_rate_limit()

        conn = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            if not database_name:
                database_name = DB_CONFIG["database"]

            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA=%s
                AND TABLE_NAME=%s
            """, (DB_CONFIG["database"], table_name))

            exists = cursor.fetchone()["COUNT(*)"]

            if exists == 0:
                raise Exception(f"Table '{table_name}' does not exist")

            # Fetch table columns
            cursor.execute("""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s
                AND TABLE_NAME=%s
            """, (DB_CONFIG["database"], table_name))

            columns = cursor.fetchall()

            return columns

        except Exception as e:
            logger.error(f"Describe table failed: {e}")
            raise

        finally:
            if conn:
                conn.close()

    @mcp.tool()
    def list_procedures(database_name: str = "mcp_demo"):
        """
        List stored procedures available in the database
        """

        check_rate_limit()

        procedures = load_procedure_metadata()

        result = []

        for proc, params in procedures.items():

            metadata = build_procedure_metadata(proc, params)

            result.append({
                "name": proc,
                "parameters": params,
                "category": metadata["category"],
                "description": metadata["description"]
            })

        return result
