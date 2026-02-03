from unittest.mock import MagicMock

import pytest

from app.controllers.account_controller import AccountController
from app.utils.exceptions import UnauthorizedException


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
    """Genera token y envía correo sin devolverlo."""
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
    sent = {"called": False, "args": None}

    def _send_reset_email(**kwargs):
        sent["called"] = True
        sent["args"] = kwargs

    monkeypatch.setattr(
        "app.controllers.account_controller.send_reset_email",
        _send_reset_email,
    )

    controller.request_password_reset(db, MagicMock(email="user@test.com"))
    assert sent["called"] is True
    assert sent["args"]["to_email"] == "user@test.com"
    assert sent["args"]["reset_token"] == "reset123"


def test_request_password_reset_not_found(monkeypatch, controller):
    """No revela existencia: no envía correo ni lanza excepción."""
    db = MagicMock()
    monkeypatch.setattr(
        controller.account_dao,
        "get_by_email",
        lambda db, email, only_active=True: None,
    )
    sent = {"called": False}
    monkeypatch.setattr(
        "app.controllers.account_controller.send_reset_email",
        lambda **kwargs: sent.update({"called": True}),
    )

    controller.request_password_reset(db, MagicMock(email="user@test.com"))
    assert sent["called"] is False


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
