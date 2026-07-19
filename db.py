import mysql.connector
from config import DB_CONFIG, MAX_QUERY_ROWS, BLOCKED_KEYWORDS
from logger import logger
import json


def get_connection():
    """
    Create and return a new database connection
    """

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def load_database_procedures():
    """
    Fetch all stored procedures from the database
    """

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ROUTINE_NAME
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_TYPE='PROCEDURE'
            AND ROUTINE_SCHEMA=%s
        """, (DB_CONFIG["database"],))

        procedures = {row[0] for row in cursor.fetchall()}

        logger.info(f"Loaded {len(procedures)} procedures from database")

        return procedures

    except Exception as e:
        logger.error(f"Failed to load procedures: {e}")
        raise

    finally:
        if conn:
            conn.close()


# Load procedures once when server starts
ALLOWED_PROCS = load_database_procedures()


def validate_procedure(proc_name):
    """
    Validate procedure name before execution
    """

    name = proc_name.lower()

    # Check procedure exists
    if proc_name not in ALLOWED_PROCS:
        logger.warning(f"Procedure not found: {proc_name}")
        raise Exception(f"Procedure {proc_name} not found in database")

    # Check restricted keywords
    for keyword in BLOCKED_KEYWORDS:
        if keyword in name:
            logger.warning(f"Blocked procedure due to keyword '{keyword}': {proc_name}")
            raise Exception(f"Procedure blocked due to restricted keyword: {keyword}")

    return True

def execute_procedure_call(proc_name, params=None):
    """
    Execute stored procedure safely
    """

    name = proc_name.lower()

    # block dangerous procedures
    for keyword in BLOCKED_KEYWORDS:
        if keyword in name:
            raise Exception(f"Procedure blocked due to restricted keyword: {keyword}")

    conn = None

    try:
        validate_procedure(proc_name)
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        logger.info(f"Calling procedure: {proc_name}")

        cursor.callproc(proc_name, params or [])

        results = []

        for result in cursor.stored_results():

            rows = result.fetchall()

            if len(rows) > MAX_QUERY_ROWS:
                rows = rows[:MAX_QUERY_ROWS]

            results.extend(rows)

        return results

    except Exception as e:

        logger.error(f"Procedure execution failed ({proc_name}): {e}")
        raise

    finally:
        if conn:
            conn.close()

def get_procedure_parameters(proc_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(""" 
        SELECT PARAMETER_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.PARAMETERS 
        WHERE SPECIFIC_NAME=%s AND SPECIFIC_SHEMA=%s ORDER BY ORDINAL POSITION """,
        (proc_name,DB_CONFIG["database"]))

    params = cursor.fetchall()
    
    conn.close()
    
    return params


def load_procedure_metadata():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT ROUTINE_NAME
        FROM INFORMATION_SCHEMA.ROUTINES
        WHERE ROUTINE_SCHEMA = %s
        AND ROUTINE_TYPE='PROCEDURE'
    """, (DB_CONFIG["database"],))

    procedures = {row["ROUTINE_NAME"]: [] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT SPECIFIC_NAME, PARAMETER_NAME
        FROM INFORMATION_SCHEMA.PARAMETERS
        WHERE SPECIFIC_SCHEMA = %s
    """, (DB_CONFIG["database"],))

    for row in cursor.fetchall():

        proc = row["SPECIFIC_NAME"]
        param = row["PARAMETER_NAME"]

        if proc in procedures and param:
            procedures[proc].append(param)

    conn.close()

    return procedures

def fetch_procedure_metadata():
    """
    Fetch procedures and parameters from INFORMATION_SCHEMA
    """

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT
            SPECIFIC_NAME,
            PARAMETER_NAME,
            DATA_TYPE,
            PARAMETER_MODE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.PARAMETERS
        WHERE SPECIFIC_SCHEMA=%s
        ORDER BY SPECIFIC_NAME, ORDINAL_POSITION
        """, (DB_CONFIG["database"],))

        rows = cursor.fetchall()

        procedures = {}

        for row in rows:

            proc = row["SPECIFIC_NAME"]
            param = row["PARAMETER_NAME"]

            if proc not in procedures:
                procedures[proc] = []

            if param:
                procedures[proc].append(param)

        return procedures

    finally:
        if conn:
            conn.close()

#Allowed databases for query execution
ALLOWED_DATABASES = ["mcp_demo", "Vegayan_BRAS"]

def validate_query(query: str):
    q = query.lower().strip()

    q = q.replace("```sql", "").replace("```", "")

    if not q.startswith("select"):
        raise Exception("Only SELECT queries are allowed")

    blocked = ["drop", "delete", "insert", "update", "alter", "truncate"]
    if any(word in q for word in blocked):
        raise Exception("Query contains restricted keywords")


def run_query(query: str, database: str = "mcp_demo"):
    """
        Execute database query """

    if database not in ALLOWED_DATABASES:
        raise Exception("Unauthorized database")

    validate_query(query)

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "limit" not in query.lower():
            query += " LIMIT 100"

        cursor.execute(query)

        rows = cursor.fetchall()

        return json.dumps(rows, default=str)

    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
