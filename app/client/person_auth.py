# app/clients/person_auth.py
from typing import Optional

import httpx

from app.core.config import settings


class PersonAuthService:
    def __init__(self):
        self._token: Optional[str] = None

    @property
    def token(self) -> Optional[str]:
        return self._token

    async def login(self) -> str:
        """Hace login en el MS de personas y guarda el token."""
        payload = {
            "email": settings.PERSON_MS_ADMIN_EMAIL,
            "password": settings.PERSON_MS_ADMIN_PASSWORD,
        }
        async with httpx.AsyncClient(base_url=settings.PERSON_MS_BASE_URL) as client:
            resp = await client.post("/api/person/login", json=payload)
            resp.raise_for_status()
            body = resp.json()
            token = body["data"]["token"]  # viene con el prefijo 'Bearer ...'
            self._token = token
            return token
