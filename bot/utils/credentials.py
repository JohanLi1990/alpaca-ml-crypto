import os

from dotenv import load_dotenv


def load_credentials() -> tuple[str, str]:
    """Load Alpaca API credentials from environment (with optional .env support).

    Returns:
        (api_key, secret_key) tuple.

    Raises:
        EnvironmentError: if either required variable is missing.
    """
    load_dotenv()  # no-op if .env absent

    required = ["APCA_API_KEY_ID", "APCA_API_SECRET_KEY"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )

    # Values are read but never logged
    api_key = os.environ["APCA_API_KEY_ID"]
    secret_key = os.environ["APCA_API_SECRET_KEY"]

    print("Credentials loaded.")
    return api_key, secret_key
