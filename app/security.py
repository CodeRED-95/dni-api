import os

from dotenv import load_dotenv
from fastapi import Header, HTTPException, status


load_dotenv()

API_KEY = os.getenv("API_KEY", "")


def verify_api_key(x_api_key: str = Header(default="")) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key no configurada en el servidor.",
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida.",
        )
