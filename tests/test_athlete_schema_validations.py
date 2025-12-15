"""
Suite de pruebas simplificadas para HS-004: Registro de Deportista Menor.

NOTA: Esta es una versión simplificada que omite las pruebas de autenticación
ya que la integración completa con el servicio de autenticación JWT aún no está implementada.

Pruebas incluidas:
- Validaciones de esquema Pydantic
- Reglas de negocio (edad, autorización parental)
- Sanitización OWASP
- Manejo de errores

TODO: Una vez implementada la autenticación JWT completa (PyJWT con OTHERS_KEY),
descomentar el archivo test_athlete_registration.py que incluye pruebas de seguridad.
"""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from app.schemas.athlete_schema import MinorAthleteCreateSchema, RepresentativeCreateSchema


# ============================================================================
# GRUPO 1: VALIDACIONES DE ESQUEMA PYDANTIC
# ============================================================================

class TestSchemaValidations:
    """Pruebas de validación a nivel de esquema Pydantic."""
    
    def test_should_accept_valid_minor_athlete_data(self):
        """
        GIVEN: Datos válidos de un menor de edad
        WHEN: Se crea el schema MinorAthleteCreateSchema
        THEN: No lanza excepción de validación
        """
        valid_data = {
            "first_name": "Juan Carlos",
            "last_name": "Pérez López",
            "dni": "12345678",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "María Elena",
                "last_name": "López García",
                "dni": "87654321",
                "address": "Av. Principal 123",
                "phone": "+593991234567",
                "email": "maria.lopez@email.com"
            }
        }
        
        schema = MinorAthleteCreateSchema(**valid_data)
        
        assert schema.first_name == "Juan Carlos"
        assert schema.dni == "12345678"
        assert schema.parental_authorization == True
        assert schema.representative.email == "maria.lopez@email.com"
    
    def test_should_reject_adult_birth_date(self):
        """
        GIVEN: Fecha de nacimiento que corresponde a mayor de 18 años
        WHEN: Se valida con el schema
        THEN: Lanza ValidationError indicando que debe ser menor de 18
        """
        adult_birth_date = (date.today() - timedelta(days=19*365)).isoformat()
        
        invalid_data = {
            "first_name": "Adulto",
            "last_name": "Test",
            "dni": "99999999",
            "birth_date": adult_birth_date,
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "88888888",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep@test.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("18 años" in str(error).lower() or "edad" in str(error).lower() for error in errors)
    
    def test_should_reject_very_young_minor(self):
        """
        GIVEN: Fecha de nacimiento menor de 5 años
        WHEN: Se valida con el schema
        THEN: Lanza ValidationError indicando edad mínima
        """
        very_young_date = (date.today() - timedelta(days=3*365)).isoformat()
        
        invalid_data = {
            "first_name": "Muy",
            "last_name": "Joven",
            "dni": "11111111",
            "birth_date": very_young_date,
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "22222222",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep@test.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("5 años" in str(error).lower() or "edad" in str(error).lower() for error in errors)
    
    def test_should_reject_without_parental_authorization(self):
        """
        GIVEN: Datos sin autorización parental (False)
        WHEN: Se valida con el schema
        THEN: Lanza ValidationError indicando que es obligatoria
        """
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "33333333",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": False,  # Inválido
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "44444444",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep@test.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("autorización" in str(error).lower() or "authorization" in str(error).lower() for error in errors)


# ============================================================================
# GRUPO 2: SANITIZACIÓN OWASP
# ============================================================================

class TestOWASPSanitization:
    """Pruebas de sanitización y prevención de inyección."""
    
    def test_should_reject_xss_in_names(self):
        """
        GIVEN: Nombre con script XSS malicioso
        WHEN: Se valida con el schema
        THEN: Rechaza por validación de formato (solo letras)
        """
        xss_data = {
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "Normal",
            "dni": "55555555",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "66666666",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep@test.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**xss_data)
        
        errors = exc_info.value.errors()
        assert any("first_name" in str(error) for error in errors)
    
    def test_should_reject_sql_injection_in_dni(self):
        """
        GIVEN: DNI con intento de inyección SQL
        WHEN: Se valida con el schema
        THEN: Rechaza por validación regex (solo alfanuméricos)
        """
        sql_injection_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "12345'; DROP TABLE athletes; --",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "77777777",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep@test.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**sql_injection_data)
        
        errors = exc_info.value.errors()
        assert any("dni" in str(error).lower() for error in errors)
    
    def test_should_reject_dangerous_chars_in_phone(self):
        """
        GIVEN: Teléfono con caracteres peligrosos
        WHEN: Se valida con el schema
        THEN: Rechaza o sanitiza
        """
        dangerous_phone_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "88888888",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "99999999",
                "address": "Calle 123",
                "phone": "+593<script>alert('xss')</script>",
                "email": "rep@test.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**dangerous_phone_data)
        
        errors = exc_info.value.errors()
        # Debe rechazar por validación de teléfono
        assert len(errors) > 0


# ============================================================================
# GRUPO 3: VALIDACIONES DE FORMATO
# ============================================================================

class TestFormatValidations:
    """Pruebas de validación de formatos de datos."""
    
    def test_should_reject_invalid_email_format(self):
        """
        GIVEN: Email sin formato válido
        WHEN: Se valida con el schema
        THEN: Lanza ValidationError
        """
        invalid_email_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "00000000",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "11111111",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "email_invalido_sin_arroba.com"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MinorAthleteCreateSchema(**invalid_email_data)
        
        errors = exc_info.value.errors()
        assert any("email" in str(error).lower() for error in errors)
    
    def test_should_accept_valid_dni_formats(self):
        """
        GIVEN: DNI con formatos válidos (números, letras, guiones)
        WHEN: Se valida con el schema
        THEN: Acepta el dato
        """
        valid_formats = ["12345678", "ABC12345", "12-34-56-78"]
        
        for dni_format in valid_formats:
            valid_data = {
                "first_name": "Test",
                "last_name": "User",
                "dni": dni_format,
                "birth_date": "2010-05-15",
                "sex": "M",
                "parental_authorization": True,
                "representative": {
                    "first_name": "Rep",
                    "last_name": "Test",
                    "dni": "REP-12345",  # Mínimo 8 caracteres
                    "address": "Calle 123",
                    "phone": "+593991234567",
                    "email": "rep@test.com"
                }
            }
            
            # No debe lanzar excepción
            schema = MinorAthleteCreateSchema(**valid_data)
            assert schema.dni == dni_format
    
    def test_should_accept_accented_characters_in_names(self):
        """
        GIVEN: Nombres con tildes y caracteres acentuados
        WHEN: Se valida con el schema
        THEN: Acepta los datos (son válidos en español)
        """
        accented_data = {
            "first_name": "José María",
            "last_name": "González Núñez",
            "dni": "22222222",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Sofía Ángela",
                "last_name": "Méndez Íñiguez",
                "dni": "33333333",
                "address": "Calle Principal",
                "phone": "+593991234567",
                "email": "sofia@test.com"
            }
        }
        
        schema = MinorAthleteCreateSchema(**accented_data)
        assert schema.first_name == "José María"
        assert schema.representative.last_name == "Méndez Íñiguez"


# ============================================================================
# GRUPO 4: VALIDACIONES DE REPRESENTATIVE
# ============================================================================

class TestRepresentativeValidations:
    """Pruebas específicas del esquema de Representante."""
    
    def test_should_accept_valid_representative_data(self):
        """
        GIVEN: Datos válidos de representante
        WHEN: Se crea el schema RepresentativeCreateSchema
        THEN: No lanza excepción
        """
        valid_rep = {
            "first_name": "María Elena",
            "last_name": "López García",
            "dni": "87654321",
            "address": "Av. Principal 123, Ciudad",
            "phone": "+593991234567",
            "email": "maria.lopez@email.com"
        }
        
        schema = RepresentativeCreateSchema(**valid_rep)
        assert schema.first_name == "María Elena"
        assert schema.email == "maria.lopez@email.com"
    
    def test_should_require_all_mandatory_fields(self):
        """
        GIVEN: Datos de representante sin campos obligatorios
        WHEN: Se intenta crear el schema
        THEN: Lanza ValidationError por campos faltantes
        """
        incomplete_data = {
            "first_name": "María",
            # Faltan: last_name, dni, address, phone, email
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RepresentativeCreateSchema(**incomplete_data)
        
        errors = exc_info.value.errors()
        # Debe reportar múltiples campos faltantes
        assert len(errors) >= 4  # last_name, dni, address, phone, email


# ============================================================================
# RESUMEN DE COBERTURA
# ============================================================================

"""
RESUMEN DE PRUEBAS IMPLEMENTADAS:

✅ TestSchemaValidations (4 pruebas):
   - Aceptación de datos válidos
   - Rechazo de mayores de 18 años
   - Rechazo de menores de 5 años
   - Rechazo sin autorización parental

✅ TestOWASPSanitization (3 pruebas):
   - Prevención XSS en nombres
   - Prevención SQL injection en DNI
   - Sanitización de teléfonos

✅ TestFormatValidations (3 pruebas):
   - Validación de formato de email
   - Aceptación de formatos válidos de DNI
   - Soporte de caracteres acentuados

✅ TestRepresentativeValidations (2 pruebas):
   - Datos válidos de representante
   - Campos obligatorios

TOTAL: 12 pruebas de validación de esquemas

NOTA: Las pruebas de integración completas (con autenticación JWT, 
      mocks de DAOs y controladores) están en test_athlete_registration.py
      pero requieren configuración adicional de autenticación.
"""
