# Guía de Ejecución de Pruebas - HS-004

## 📋 Descripción General

Suite completa de pruebas unitarias e integración para el registro de deportistas menores de edad (HS-004). Incluye validación de autenticación, reglas de negocio, sanitización OWASP y manejo de errores.

## 🧪 Estructura de Pruebas

```
tests/
├── conftest.py                      # Fixtures compartidas (mocks de DB y autenticación)
├── test_athlete_registration.py    # Suite principal de HS-004
├── controllers/
│   └── test_user_controller.py     # Pruebas existentes
└── routers/
    └── test_user_router.py         # Pruebas existentes
```

## 📦 Dependencias Requeridas

Asegúrate de tener instaladas las siguientes librerías en tu entorno virtual:

```bash
# Instalación con uv (recomendado)
uv pip install pytest pytest-asyncio httpx

# O con pip tradicional
pip install pytest pytest-asyncio httpx
```

## 🚀 Ejecución de Pruebas

### 1. Ejecutar Toda la Suite de HS-004

```bash
# Desde el directorio raíz del proyecto
pytest tests/test_athlete_registration.py -v

# Con detalles extendidos
pytest tests/test_athlete_registration.py -v -s
```

### 2. Ejecutar Grupos Específicos de Pruebas

```bash
# Solo pruebas de happy path (casos exitosos)
pytest tests/test_athlete_registration.py::TestHappyPath -v

# Solo pruebas de seguridad/autenticación
pytest tests/test_athlete_registration.py::TestSecurityValidation -v

# Solo pruebas de reglas de negocio
pytest tests/test_athlete_registration.py::TestBusinessRules -v

# Solo pruebas de sanitización OWASP
pytest tests/test_athlete_registration.py::TestOWASPSanitization -v

# Solo pruebas de manejo de errores
pytest tests/test_athlete_registration.py::TestErrorHandling -v

# Solo pruebas de auditoría
pytest tests/test_athlete_registration.py::TestAuditLogging -v
```

### 3. Ejecutar una Prueba Individual

```bash
# Ejemplo: Solo la prueba de registro exitoso
pytest tests/test_athlete_registration.py::TestHappyPath::test_should_register_minor_athlete_successfully -v

# Ejemplo: Solo la prueba de DNI duplicado
pytest tests/test_athlete_registration.py::TestBusinessRules::test_should_reject_duplicate_dni_athlete -v
```

### 4. Ejecutar Todas las Pruebas del Proyecto

```bash
# Ejecutar todo el suite de tests
pytest tests/ -v

# Con resumen de cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

## 📊 Reporte de Cobertura

### Generar Reporte HTML

```bash
# Instalar pytest-cov si no lo tienes
uv pip install pytest-cov

# Generar reporte HTML interactivo
pytest tests/test_athlete_registration.py \
    --cov=app.controllers.athlete_controller \
    --cov=app.services.routers.inscription_router \
    --cov=app.schemas.athlete_schema \
    --cov-report=html

# Ver el reporte (se genera en htmlcov/index.html)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Generar Reporte en Terminal

```bash
pytest tests/test_athlete_registration.py \
    --cov=app \
    --cov-report=term-missing \
    -v
```

## 🎯 Casos de Prueba Cubiertos

### ✅ Happy Path (2 pruebas)
- `test_should_register_minor_athlete_successfully`: Registro exitoso completo
- `test_should_reuse_existing_representative`: Reutilización de representante existente

### 🔒 Seguridad y Autenticación (3 pruebas)
- `test_should_reject_request_without_token`: Sin token JWT
- `test_should_reject_request_with_invalid_token`: Token inválido/corrupto
- `test_should_reject_inactive_user`: Usuario inactivo

### 📋 Reglas de Negocio (4 pruebas)
- `test_should_reject_athlete_over_18_years_old`: Mayor de 18 años
- `test_should_reject_without_parental_authorization`: Sin autorización parental
- `test_should_reject_duplicate_dni_athlete`: DNI duplicado
- `test_should_reject_minor_under_5_years`: Menor de 5 años

### 🛡️ Sanitización OWASP (3 pruebas)
- `test_should_sanitize_or_reject_xss_in_names`: Prevención XSS en nombres
- `test_should_sanitize_or_reject_sql_injection_in_dni`: Prevención SQL injection
- `test_should_sanitize_phone_with_special_chars`: Sanitización de teléfono

### ⚠️ Manejo de Errores (3 pruebas)
- `test_should_handle_database_error_gracefully`: Error de base de datos
- `test_should_validate_email_format`: Validación de email
- `test_should_validate_sex_field_values`: Validación de campo sexo

### 📝 Auditoría (1 prueba)
- `test_should_log_registration_with_user_info`: Logging con info de usuario

**TOTAL: 16 pruebas completas**

## 🔧 Configuración de Entorno

### Archivo pytest.ini (Opcional)

Crea un archivo `pytest.ini` en la raíz del proyecto:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Variables de Entorno para Testing

Asegúrate de que tu archivo `.env` tenga configuraciones apropiadas para testing:

```env
# Configuración de testing (opcional)
TESTING=True
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_db
OTHERS_KEY=1234567FDUCAMETB
```

## 📈 Métricas de Calidad Esperadas

Para aprobar el QA, la suite debe cumplir:

- ✅ **Cobertura mínima**: 80% en controladores y routers de HS-004
- ✅ **Todas las pruebas pasan**: 16/16 exitosas
- ✅ **Sin warnings críticos**: 0 advertencias de seguridad
- ✅ **Tiempo de ejecución**: < 5 segundos para toda la suite

## 🐛 Troubleshooting

### Error: "No module named 'app.core.security'"

**Solución**: Asegúrate de que el archivo `app/core/security.py` existe. Si no, significa que no se completó la integración de autenticación.

```bash
# Verificar que existe
ls -la app/core/security.py
```

### Error: "ImportError: cannot import name 'CurrentUser'"

**Solución**: Actualiza `app/core/security.py` para incluir la clase `CurrentUser`.

### Error: "ModuleNotFoundError: No module named 'jwt'"

**Solución**: Instalar PyJWT:

```bash
uv pip install "PyJWT[crypto]"
```

### Error: "RuntimeWarning: coroutine was never awaited"

**Solución**: Asegúrate de que las pruebas asíncronas tengan el decorador `@pytest.mark.asyncio`.

### Las pruebas de autenticación fallan

**Solución**: Verifica que:
1. El endpoint esté protegido con `Depends(get_current_user)`
2. Las fixtures de override estén configuradas correctamente
3. El módulo `security.py` esté importado sin errores

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Run HS-004 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -r requirements.txt
        uv pip install pytest pytest-asyncio pytest-cov httpx
    
    - name: Run HS-004 tests
      run: |
        pytest tests/test_athlete_registration.py -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 📚 Recursos Adicionales

- [Documentación oficial de pytest](https://docs.pytest.org/)
- [pytest-asyncio para testing asíncrono](https://github.com/pytest-dev/pytest-asyncio)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## 📞 Contacto y Soporte

Para problemas con las pruebas, contactar al equipo de QA o revisar:
- Plan de integración: `PLAN_INTEGRACION_AUTH.md`
- Documentación de registro de menores: `REGISTRO_MENORES_DOC.md`
- Issues en el repositorio del proyecto
