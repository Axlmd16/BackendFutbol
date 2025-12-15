import pytest

import importlib

account_router_module = importlib.import_module("app.services.routers.account_router")


class _MockResponse:
	"""Simula una respuesta HTTP para pruebas."""
	def __init__(self, status_code=200, json_data=None, text=""):
		"""Simula una respuesta HTTP para pruebas."""
		self.status_code = status_code
		self._json_data = json_data or {}
		self.text = text
		self.headers = {}

	def raise_for_status(self):
		"""Simula la elevación de una excepción para códigos de estado HTTP erróneos."""
		if self.status_code >= 400:
			raise Exception(self.text)

	def json(self):
		"""Devuelve los datos JSON simulados."""
		return self._json_data


class _Account:
	"""Simula una cuenta de usuario para pruebas."""
	def __init__(self, account_id=2, role="Coach", external="ext-123"):
		self.id = account_id
		self.role = role
		self.external_account_id = external


@pytest.mark.asyncio
async def test_login_success(client, monkeypatch):
	"""Prueba login exitoso: devuelve access y refresh tokens."""
	
	def fake_post(url, json, timeout):
		"""Simula una llamada HTTP POST para el inicio de sesión."""
		return _MockResponse(
			status_code=200,
			json_data={"data": {"external": "ext-123", "token": "Bearer ms-token"}},
		)

	monkeypatch.setattr(account_router_module.httpx, "post", fake_post)


	mock_controller = account_router_module.account_controller
	monkeypatch.setattr(
		mock_controller, "get_by_external", lambda db, external: _Account(account_id=2, role="Coach", external=external)
	)

	resp = await client.post(
		"/api/v1/accounts/login",
		json={"email": "user@test.com", "password": "secretpass"},
	)

	assert resp.status_code == 200
	body = resp.json()
	assert body["status"] == "success"
	assert body["data"]["external_account_id"] == "ext-123"
	assert "access_token" in body["data"]
	assert body["data"].get("refresh_token")
	assert body["data"].get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_forgot_password_generates_token(client, monkeypatch):
	"""Prueba la generación de token de recuperación de contraseña."""
	mock_controller = account_router_module.account_controller
	monkeypatch.setattr(
		mock_controller, "get_account", lambda db, account_id: _Account(account_id=account_id, external="ext-abc")
	)

	resp = await client.post(
		"/api/v1/accounts/forgot-password",
		json={"account_id": 99},
	)

	assert resp.status_code == 200
	token = resp.json()["data"]["reset_token"]
	assert token
	
	account_router_module.reset_tokens_store.clear()


@pytest.mark.asyncio
async def test_reset_password_success(client, monkeypatch):
	"""Prueba el flujo de restablecimiento de contraseña exitoso."""
	account_router_module.reset_tokens_store.clear()
	token = "tok123456789012345678901234567890"
	account_router_module.reset_tokens_store[token] = {
		"external": "ext-123",
		"expires_at": account_router_module.datetime.utcnow() + account_router_module.timedelta(hours=1),
	}

	
	account_router_module.person_auth_service._token = "Bearer admin"

	def fake_post(url, headers, json, timeout):
		"""Simula una llamada HTTP POST para actualizar la contraseña."""
		return _MockResponse(status_code=200, json_data={"status": "success"})

	monkeypatch.setattr(account_router_module.httpx, "post", fake_post)

	resp = await client.post(
		"/api/v1/accounts/reset-password",
		json={
			"token": token,
			"new_password": "newpass123",
			"confirm_password": "newpass123",
		},
	)

	assert resp.status_code == 200
	assert resp.json()["status"] == "success"
	account_router_module.reset_tokens_store.clear()


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
	"""Prueba el manejo de un token de restablecimiento de contraseña inválido."""
	account_router_module.reset_tokens_store.clear()

	resp = await client.post(
		"/api/v1/accounts/reset-password",
		json={
			"token": "bad-token-123456789012345678901234567",
			"new_password": "newpass123",
			"confirm_password": "newpass123",
		},
	)

	assert resp.status_code == 400
	assert "Token" in resp.json()["detail"] or resp.json()["status"] == "error"


@pytest.mark.asyncio
async def test_refresh_tokens_success(client):
	"""Prueba que /accounts/refresh devuelve nuevos tokens a partir de un refresh válido."""
	refresh_token = account_router_module.auth.create_refresh_token(subject="2", role="Coach")

	resp = await client.post(
		"/api/v1/accounts/refresh",
		json={"refresh_token": refresh_token},
	)

	assert resp.status_code == 200
	body = resp.json()
	assert body["status"] == "success"
	assert body["data"].get("access_token")
	assert body["data"].get("refresh_token")
	assert body["data"].get("role") == "Coach"
	assert body["data"].get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_refresh_tokens_invalid(client):
	"""Prueba que un refresh token inválido devuelve 401."""
	resp = await client.post(
		"/api/v1/accounts/refresh",
		json={"refresh_token": "token-invalido"},
	)

	assert resp.status_code == 401
	body = resp.json()
	assert "token" in body.get("detail", "").lower() or body.get("status") == "error"


@pytest.mark.asyncio
async def test_logout(client):
	"""Prueba que /accounts/logout responde éxito lógico de cierre de sesión."""
	resp = await client.post("/api/v1/accounts/logout")

	assert resp.status_code == 200
	body = resp.json()
	assert body["status"] == "success"
	assert body["data"].get("revoked") is True
