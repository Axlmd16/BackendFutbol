from unittest.mock import MagicMock

import pytest

from app.controllers.account_controller import AccountController
from app.utils.exceptions import NotFoundException, UnauthorizedException


@pytest.fixture
def controller():
    """Instancia del AccountController para pruebas."""
    return AccountController()


def _mock_account():
    """Crea una cuenta mock para pruebas."""
    acc = MagicMock()
    acc.id = 1
    acc.email = "user@test.com"
    acc.role.value = "Administrator"
    acc.password_hash = "hashed"
    return acc


def test_login_success(monkeypatch, controller):
    """Prueba de login exitoso."""
    db = MagicMock()
    account = _mock_account()

    monkeypatch.setattr(
        controller.account_dao,
        "get_by_email",
        lambda db, email, only_active=True: account,
    )
    monkeypatch.setattr(
        "app.controllers.account_controller.verify_password", lambda password, ph: True
    )
    monkeypatch.setattr(
        "app.controllers.account_controller.create_access_token",
        lambda **kwargs: "token123",
    )

    resp = controller.login(
        db, MagicMock(email="USER@test.com", password="Password123!")
    )

    assert resp.access_token == "token123"
    assert resp.token_type == "bearer"


def test_login_not_found(monkeypatch, controller):
    """Prueba de login con cuenta no encontrada."""
    db = MagicMock()
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_email",
        lambda db, email, only_active=True: None,
    )

    with pytest.raises(UnauthorizedException):
        controller.login(db, MagicMock(email="user@test.com", password="pass"))


def test_login_bad_password(monkeypatch, controller):
    """Prueba de login con contraseña incorrecta."""
    db = MagicMock()
    account = _mock_account()
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_email",
        lambda db, email, only_active=True: account,
    )
    monkeypatch.setattr(
        "app.controllers.account_controller.verify_password", lambda password, ph: False
    )

    with pytest.raises(UnauthorizedException):
        controller.login(db, MagicMock(email="user@test.com", password="wrong"))


def test_request_password_reset_success(monkeypatch, controller):
    """Prueba de solicitud de reseteo de contraseña exitoso."""
    db = MagicMock()
    account = _mock_account()
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_email",
        lambda db, email, only_active=True: account,
    )
    monkeypatch.setattr(
        "app.controllers.account_controller.create_reset_token",
        lambda *args, **kwargs: "reset123",
    )

    token = controller.request_password_reset(db, MagicMock(email="user@test.com"))
    assert token == "reset123"


def test_request_password_reset_not_found(monkeypatch, controller):
    """Prueba de solicitud de reseteo de contraseña con cuenta no encontrada."""
    db = MagicMock()
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_email",
        lambda db, email, only_active=True: None,
    )

    with pytest.raises(NotFoundException):
        controller.request_password_reset(db, MagicMock(email="user@test.com"))


def test_confirm_password_reset_success(monkeypatch, controller):
    """Prueba de confirmación de reseteo de contraseña exitoso."""
    db = MagicMock()
    account = _mock_account()
    monkeypatch.setattr(
        "app.controllers.account_controller.validate_reset_token",
        lambda token: {"sub": 1, "action": "reset_password"},
    )
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_id",
        lambda db, id, only_active=True: account,
    )
    monkeypatch.setattr(
        "app.controllers.account_controller.hash_password", lambda pwd: "new_hashed"
    )

    controller.confirm_password_reset(
        db, MagicMock(token="reset123", new_password="NewPass123!")
    )

    assert account.password_hash == "new_hashed"
    db.commit.assert_called_once()


def test_confirm_password_reset_invalid_account(monkeypatch, controller):
    """Prueba de confirmación de reseteo de contraseña con cuenta inválida."""
    db = MagicMock()
    monkeypatch.setattr(
        "app.controllers.account_controller.validate_reset_token",
        lambda token: {"sub": 99, "action": "reset_password"},
    )
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_id",
        lambda db, id, only_active=True: None,
    )

    with pytest.raises(UnauthorizedException):
        controller.confirm_password_reset(
            db, MagicMock(token="reset123", new_password="NewPass123!")
        )
