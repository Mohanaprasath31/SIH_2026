import os
from typing import Any, Optional
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

try:
    from supabase import create_client, Client
except ImportError:
    Client = Any  # type: ignore


def get_supabase_client() -> Optional[Any]:
    """
    Initializes and returns the Supabase client using environment variables.
    Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from .env.
    """
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
    )

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        print(f"[!] Error initializing Supabase client: {e}")
        return None