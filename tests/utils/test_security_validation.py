import pytest

from app.utils.exceptions import ValidationException
from app.utils.security import validate_ec_dni


def test_validate_ec_dni_success():
    """Prueba que un DNI válido pase la validación."""
    # 1710034065 es un DNI válido (módulo 10 correcto)
    assert validate_ec_dni("1710034065") == "1710034065"


def test_validate_ec_dni_invalid_check_digit():
    """Prueba que un DNI con dígito verificador incorrecto ."""
    # 1710034066 tiene el mismo prefijo pero dígito verificador incorrecto
    with pytest.raises(ValidationException) as exc:
        validate_ec_dni("1710034066")

    assert str(exc.value) == "Dni invalido"


def test_validate_ec_dni_invalid_length():
    """Prueba validación de longitud."""
    with pytest.raises(ValidationException) as exc:
        validate_ec_dni("123")
    assert str(exc.value) == "El DNI debe tener exactamente 10 digitos"
