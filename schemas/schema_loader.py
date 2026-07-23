import os
from logger import logger

def load_schema(db_name : str) -> str:
    schema_file_name = f"{db_name}.schema"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(current_dir, schema_file_name)

    try:
        with open(schema_file, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Schema file {schema_file_name} not available")
        return None
    except Exception as e:
        logger.error(f"Could not load schema from {schema_file_name}: {str(e)}")
        return None