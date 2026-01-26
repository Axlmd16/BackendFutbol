from typing import Any, Dict, List, Optional

import httpx

from app.client.person_auth import PersonAuthService
from app.core.config import settings
from app.utils.exceptions import ExternalServiceException, ValidationException

auth_service = PersonAuthService()


class PersonClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url or settings.PERSON_MS_BASE_URL
        self.timeout = timeout

    async def _authorized_request(self, method: str, url: str, **kwargs) -> Any:
        """
        Realiza una petición autenticada al MS de usuarios.
        Maneja errores de conexión y autenticación.
        """
        try:
            token = auth_service.token or await auth_service.login()
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ConnectTimeout,
        ) as e:
            raise ExternalServiceException(
                "El servicio de usuarios no está disponible. "
                "Por favor, intente nuevamente más tarde."
            ) from e

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = token

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            ) as client:
                resp = await client.request(method, url, headers=headers, **kwargs)

                if resp.status_code == 401:
                    token = await auth_service.login()
                    headers["Authorization"] = token
                    resp = await client.request(method, url, headers=headers, **kwargs)

                if resp.status_code >= 400:
                    try:
                        error_data = resp.json()
                        if isinstance(error_data, dict):
                            error_message = (
                                error_data.get("message")
                                or error_data.get("detail")
                                or error_data.get("error")
                                or "Error desconocido"
                            )
                        elif isinstance(error_data, list) and error_data:
                            # FastAPI/Pydantic suele devolver una lista de errores.
                            first = error_data[0]
                            if isinstance(first, dict):
                                error_message = (
                                    first.get("message")
                                    or first.get("detail")
                                    or first.get("msg")
                                    or "Error desconocido"
                                )
                            else:
                                error_message = str(first)
                        else:
                            error_message = "Error desconocido"
                    except Exception:
                        error_message = resp.text or f"Error {resp.status_code}"

                    raise ValidationException(error_message)

                return resp.json()

        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ConnectTimeout,
        ) as e:
            raise ExternalServiceException(
                "El servicio de usuarios no está disponible. "
                "Por favor, intente nuevamente más tarde."
            ) from e

    async def create_person(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request("POST", "/api/person/save", json=data)

    async def create_person_with_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request(
            "POST", "/api/person/save-account", json=data
        )

    async def update_person(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request("POST", "/api/person/update", json=data)

    async def update_person_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request(
            "POST", "/api/person/update-account", json=data
        )

    async def get_by_id(self, person_id: int) -> Dict[str, Any]:
        return await self._authorized_request(
            "GET", f"/api/person/search_id/{person_id}"
        )

    async def get_by_identification(self, identification: str) -> Dict[str, Any]:
        return await self._authorized_request(
            "GET", f"/api/person/search_identification/{identification}"
        )

    async def get_by_external(self, external: str) -> Dict[str, Any]:
        return await self._authorized_request("GET", f"/api/person/search/{external}")

    async def change_state(self, external: str) -> Dict[str, Any]:
        return await self._authorized_request(
            "GET", f"/api/person/change_state/{external}"
        )

    async def get_all_filter(self) -> List[Dict[str, Any]]:
        return await self._authorized_request("GET", "/api/person/all_filter")
