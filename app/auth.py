import os

from dotenv import load_dotenv
from fastapi_plugin.fast_api_client import Auth0FastAPI


load_dotenv()


def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


auth0 = Auth0FastAPI(
    domain=required_setting("AUTH0_DOMAIN"),
    audience=required_setting("AUTH0_AUDIENCE"),
)

require_auth = auth0.require_auth()
