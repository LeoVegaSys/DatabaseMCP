from logger import logger
from schemas.schema_loader import load_schema

def register_discovery_resources(mcp):
    
    @mcp.resource("schema://{db_name}")
    def get_schema(db_name: str) -> str:
        """
        Provide database schema as resource
        """
        logger.info(f"Retrieving {db_name} schema")
        return load_schema(db_name)
