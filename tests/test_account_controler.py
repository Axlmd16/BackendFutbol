"""Pruebas unitarias básicas para AccountController (en español)."""

import pytest
from unittest.mock import MagicMock

from app.controllers.account_controller import AccountController


class DummyAccount:
	"""Simula una cuenta de usuario para pruebas."""
	def __init__(self, external_account_id="ext-123"):
		self.external_account_id = external_account_id


def test_get_by_external_calls_dao(monkeypatch):
	"""Prueba que AccountController.get_by_external llama a AccountDAO.get_by_external con los parámetros correctos."""
	dao_mock = MagicMock()
	dao_mock.get_by_external.return_value = DummyAccount()

	controller = AccountController()
	controller.account_dao = dao_mock

	db = MagicMock()
	result = controller.get_by_external(db, "ext-123", only_active=False)

	dao_mock.get_by_external.assert_called_once_with(db, "ext-123", only_active=False)
	assert isinstance(result, DummyAccount)
