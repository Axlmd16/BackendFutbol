import httpx
from typing import Any, Dict, List, Optional
from app.client.person_auth import PersonAuthService
from app.core.config import settings

auth_service = PersonAuthService()

class PersonClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url or settings.PERSON_MS_BASE_URL
        self.timeout = timeout

    async def _authorized_request(self, method: str, url: str, **kwargs) -> Any:
        # 1) Asegurar token
        token = auth_service.token or await auth_service.login()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = token   # ya incluye 'Bearer ...'

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.request(method, url, headers=headers, **kwargs)

            # Si el token expira y el MS responde 401, reintentar una vez con login nuevo
            if resp.status_code == 401:
                token = await auth_service.login()
                headers["Authorization"] = token
                resp = await client.request(method, url, headers=headers, **kwargs)

            resp.raise_for_status()
            return resp.json()

    async def create_person(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request("POST", "/api/person/save", json=data)

    async def create_person_with_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request("POST", "/api/person/save-account", json=data)

    async def update_person(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request("POST", "/api/person/update", json=data)

    async def update_person_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._authorized_request("POST", "/api/person/update-account", json=data)

    async def get_by_id(self, person_id: int) -> Dict[str, Any]:
        return await self._authorized_request("GET", f"/api/person/search_id/{person_id}")

    async def get_by_identification(self, identification: str) -> Dict[str, Any]:
        return await self._authorized_request("GET", f"/api/person/search_identification/{identification}")

    async def get_by_external(self, external: str) -> Dict[str, Any]:
        return await self._authorized_request("GET", f"/api/person/search/{external}")

    async def change_state(self, external: str) -> Dict[str, Any]:
        return await self._authorized_request("GET", f"/api/person/change_state/{external}")

    async def get_all_filter(self) -> List[Dict[str, Any]]:
        return await self._authorized_request("GET", "/api/person/all_filter")
