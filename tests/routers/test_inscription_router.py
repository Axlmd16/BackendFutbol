"""Tests para el router de inscripción de deportistas UNL."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_register_athlete_unl_success(client, mock_db_session):
    """Test: Registrar deportista UNL exitosamente."""
    
    # Mock: Crear un deportista simulado
    mock_athlete = MagicMock()
    mock_athlete.id = 1
    mock_athlete.first_name = "Juan"
    mock_athlete.last_name = "Pérez"
    mock_athlete.institutional_email = "juan.perez@unl.edu.ec"
    
    # Mock: Crear estadísticas simuladas
    mock_statistic = MagicMock()
    mock_statistic.id = 1
    
    # Mock de los DAOs a nivel de instancia
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    with patch("app.dao.athlete_dao.AthleteDAO.exists", return_value=False), \
         patch("app.dao.athlete_dao.AthleteDAO.create", return_value=mock_athlete), \
         patch("app.dao.statistic_dao.StatisticDAO.create", return_value=mock_statistic):
        
        # Request
        response = await client.post(
            "/api/v1/inscription/deportista",
            json={
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "phone": "0987654321",
                "birth_date": "1998-05-15",
                "institutional_email": "juan.perez@unl.edu.ec",
                "university_role": "STUDENT",
                "weight": "75.5",
                "height": "180"
            }
        )
        
        # Assertions
        assert response.status_code == 201
        assert response.json()["status"] == "success"
        assert response.json()["data"]["athlete_id"] == 1


@pytest.mark.asyncio
async def test_register_athlete_invalid_role(client, mock_db_session):
    """Test: Rechazar deportista con estamento inválido."""
    
    response = await client.post(
        "/api/v1/inscription/deportista",
        json={
            "first_name": "Juan",
            "last_name": "Pérez",
            "dni": "1710034065",
            "phone": "0987654321",
            "birth_date": "1998-05-15",
            "institutional_email": "juan.perez@unl.edu.ec",
            "university_role": "INVALID_ROLE",
            "weight": "75.5",
            "height": "180"
        }
    )
    
    # Assertions: la validación de rol debe responder con 400
    assert response.status_code == 400
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
async def test_register_athlete_duplicate_dni(client, mock_db_session):
    """Test: Rechazar deportista con DNI duplicado."""
    
    with patch("app.dao.athlete_dao.AthleteDAO.exists", return_value=True):
        
        response = await client.post(
            "/api/v1/inscription/deportista",
            json={
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "phone": "0987654321",
                "birth_date": "1998-05-15",
                "institutional_email": "juan.perez@unl.edu.ec",
                "university_role": "STUDENT",
                "weight": "75.5",
                "height": "180"
            }
        )
        
        # Assertions
        assert response.status_code == 409
        assert response.json()["status"] == "error"
        assert "ya existe" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_register_athlete_duplicate_email(client, mock_db_session):
    """Test: Rechazar deportista con email duplicado."""
    
    with patch("app.dao.athlete_dao.AthleteDAO.exists") as mock_exists:
        
        # Mock: Primera llamada (DNI) no existe, segunda (email) sí existe
        mock_exists.side_effect = [False, True]
        
        response = await client.post(
            "/api/v1/inscription/deportista",
            json={
                "first_name": "Juan",
                "last_name": "Pérez",
                "dni": "1710034065",
                "phone": "0987654321",
                "birth_date": "1998-05-15",
                "institutional_email": "juan.perez@unl.edu.ec",
                "university_role": "STUDENT",
                "weight": "75.5",
                "height": "180"
            }
        )
        
        # Assertions
        assert response.status_code == 409
        assert response.json()["status"] == "error"
        assert "email" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_register_athlete_invalid_dni_format(client, mock_db_session):
    """Test: Rechazar deportista con DNI inválido."""
    
    response = await client.post(
        "/api/v1/inscription/deportista",
        json={
            "first_name": "Juan",
            "last_name": "Pérez",
            "dni": "123",  # DNI inválido (menos de 10 dígitos)
            "phone": "0987654321",
            "birth_date": "1998-05-15",
            "institutional_email": "juan.perez@unl.edu.ec",
            "university_role": "STUDENT",
            "weight": "75.5",
            "height": "180"
        }
    )
    
    # Assertions: Validación de DNI debería rechazarlo
    assert response.status_code == 400
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
async def test_register_athlete_missing_required_fields(client, mock_db_session):
    """Test: Rechazar solicitud con campos faltantes."""
    
    response = await client.post(
        "/api/v1/inscription/deportista",
        json={
            "first_name": "Juan",
            # Falta last_name
            "institutional_email": "juan.perez@unl.edu.ec",
            "university_role": "STUDENT",
        }
    )
    
    # Assertions
    assert response.status_code == 422  # Validación de Pydantic


@pytest.mark.asyncio
async def test_register_athlete_all_valid_roles(client, mock_db_session):
    """Test: Aceptar todos los roles válidos (STUDENT, TEACHER, ADMIN, WORKER)."""
    
    valid_roles = ["STUDENT", "TEACHER", "ADMIN", "WORKER"]
    
    for role in valid_roles:
        mock_athlete = MagicMock()
        mock_athlete.id = 1
        mock_athlete.first_name = "Juan"
        mock_athlete.last_name = "Pérez"
        mock_athlete.institutional_email = f"juan.{role.lower()}@unl.edu.ec"
        
        mock_statistic = MagicMock()
        mock_statistic.id = 1
        
        with patch("app.dao.athlete_dao.AthleteDAO.exists", return_value=False), \
             patch("app.dao.athlete_dao.AthleteDAO.create", return_value=mock_athlete), \
             patch("app.dao.statistic_dao.StatisticDAO.create", return_value=mock_statistic):
            
            response = await client.post(
                "/api/v1/inscription/deportista",
                json={
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "dni": "1710034065",
                    "phone": "0987654321",
                    "birth_date": "1998-05-15",
                    "institutional_email": f"juan.{role.lower()}@unl.edu.ec",
                    "university_role": role,
                    "weight": "75.5",
                    "height": "180"
                }
            )
            
            # Assertion
            assert response.status_code == 201
            assert response.json()["status"] == "success"
