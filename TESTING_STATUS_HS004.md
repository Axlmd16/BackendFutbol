# Suite de Pruebas - HS-004: Registro de Deportista Menor

## 📊 Estado Actual

✅ **12 pruebas de validación de esquemas - TODAS PASANDO**

```bash
========================== 12 passed in 0.05s ==========================
```

## 📁 Archivos Creados

### 1. Pruebas Funcionales
- **`tests/test_athlete_schema_validations.py`** ✅
  - 12 pruebas de validación Pydantic
  - Cobertura de reglas de negocio
  - Sanitización OWASP
  - Validaciones de formato
  - **Estado**: COMPLETADO Y FUNCIONANDO

### 2. Pruebas de Integración (Requiere Configuración Adicional)
- **`tests/test_athlete_registration.py`** ⚠️
  - 16 pruebas completas de integración
  - Incluye autenticación JWT
  - Mocks de DAOs y controladores
  - **Estado**: CREADO, pendiente de configuración de autenticación

### 3. Infraestructura de Testing
- **`tests/conftest.py`** ✅
  - Fixtures de mock de BD
  - Cliente HTTP asíncrono
  - Mock de CurrentUser
  - **Estado**: ACTUALIZADO

### 4. Módulo de Seguridad
- **`app/core/security.py`** ✅
  - Clase CurrentUser
  - Dependencia get_current_user (básica)
  - HTTPBearer security
  - **Estado**: IMPLEMENTACIÓN BÁSICA (requiere PyJWT para producción)

- **`app/utils/security.py`** ✅
  - Clase CurrentUser (también disponible aquí)
  - Validaciones de DNI
  - Validaciones de email
  - **Estado**: ACTUALIZADO

### 5. Documentación
- **`TESTING_GUIDE_HS004.md`** ✅
  - Guía completa de ejecución
  - Comandos pytest
  - Troubleshooting
  - Integración CI/CD
  - **Estado**: DOCUMENTACIÓN COMPLETA

## 🎯 Cobertura de Pruebas

### ✅ Pruebas Implementadas y Funcionando (12)

#### Grupo 1: Validaciones de Esquema (4 pruebas)
1. ✅ `test_should_accept_valid_minor_athlete_data` - Datos válidos
2. ✅ `test_should_reject_adult_birth_date` - Mayor de 18 años
3. ✅ `test_should_reject_very_young_minor` - Menor de 5 años
4. ✅ `test_should_reject_without_parental_authorization` - Sin autorización

#### Grupo 2: Sanitización OWASP (3 pruebas)
5. ✅ `test_should_reject_xss_in_names` - XSS en nombres
6. ✅ `test_should_reject_sql_injection_in_dni` - SQL injection en DNI
7. ✅ `test_should_reject_dangerous_chars_in_phone` - Chars peligrosos en teléfono

#### Grupo 3: Validaciones de Formato (3 pruebas)
8. ✅ `test_should_reject_invalid_email_format` - Email inválido
9. ✅ `test_should_accept_valid_dni_formats` - Formatos DNI válidos
10. ✅ `test_should_accept_accented_characters_in_names` - Tildes en nombres

#### Grupo 4: Validaciones de Representante (2 pruebas)
11. ✅ `test_should_accept_valid_representative_data` - Datos válidos
12. ✅ `test_should_require_all_mandatory_fields` - Campos obligatorios

### ⚠️ Pruebas Pendientes de Configuración (16)

Archivo: `test_athlete_registration.py`

**Requieren**: Integración completa de autenticación JWT con PyJWT

- Happy Path (2 pruebas)
- Seguridad/Autenticación (3 pruebas)
- Reglas de Negocio (4 pruebas)
- Sanitización OWASP (3 pruebas)
- Manejo de Errores (3 pruebas)
- Auditoría/Logging (1 prueba)

## 🚀 Ejecución Rápida

### Ejecutar pruebas que funcionan actualmente:

```bash
# Todas las pruebas de validación (12)
pytest tests/test_athlete_schema_validations.py -v

# Solo sanitización OWASP
pytest tests/test_athlete_schema_validations.py::TestOWASPSanitization -v

# Con cobertura
pytest tests/test_athlete_schema_validations.py --cov=app.schemas -v
```

### Verificar estado del proyecto:

```bash
# Ver todas las pruebas disponibles
pytest tests/test_athlete_schema_validations.py --collect-only

# Ejecutar con detalles
pytest tests/test_athlete_schema_validations.py -v -s
```

## 📋 Próximos Pasos para Habilitar Todas las Pruebas

### 1. Instalar PyJWT
```bash
uv pip install "PyJWT[crypto]"
# o
pip install "PyJWT[crypto]"
```

### 2. Configurar Variable de Entorno
Agregar a `.env`:
```env
OTHERS_KEY=1234567FDUCAMETB
```

### 3. Implementar Validación JWT Completa
Actualizar `app/core/security.py` con:
- Decodificación de token con PyJWT
- Validación de firma con OTHERS_KEY
- Manejo de tokens expirados
- Extracción de claims del usuario

### 4. Ejecutar Pruebas de Integración
```bash
pytest tests/test_athlete_registration.py -v
```

## 📈 Métricas de Calidad

### Actuales
- ✅ 12/12 pruebas de validación pasando (100%)
- ✅ 0 errores en esquemas Pydantic
- ✅ Sanitización OWASP validada
- ✅ Tiempo de ejecución: < 0.1s

### Objetivo Final
- 🎯 28/28 pruebas totales (12 validación + 16 integración)
- 🎯 Cobertura > 80% en módulos de HS-004
- 🎯 Autenticación JWT funcional
- 🎯 Tiempo total: < 5s

## 🔍 Estructura de Testing

```
tests/
├── conftest.py                           # Fixtures compartidas
├── test_athlete_schema_validations.py    # ✅ 12 pruebas funcionando
├── test_athlete_registration.py          # ⚠️ 16 pruebas (requiere JWT)
├── controllers/
│   └── test_user_controller.py
└── routers/
    └── test_user_router.py
```

## 🛡️ Validaciones Cubiertas

### ✅ Seguridad OWASP
- Prevención de XSS en campos de texto
- Prevención de SQL injection en DNI
- Sanitización de inputs de teléfono
- Validación estricta de emails

### ✅ Reglas de Negocio
- Edad entre 5 y 17 años
- Autorización parental obligatoria (True)
- Formatos de DNI válidos (alfanuméricos y guiones)
- Soporte de caracteres acentuados

### ✅ Integridad de Datos
- Campos obligatorios de representante
- Formatos de email válidos
- Longitudes mínimas de DNI (8 caracteres)
- Tipos de datos correctos

## 📞 Soporte

Para más información, consultar:
- `TESTING_GUIDE_HS004.md` - Guía completa de testing
- `PLAN_INTEGRACION_AUTH.md` - Integración con auth service
- `REGISTRO_MENORES_DOC.md` - Documentación del feature

## 🎉 Resumen

**Estado del proyecto de testing para HS-004:**

✅ **Fase 1 Completada**: Validaciones de esquema Pydantic (12 pruebas)
⚠️ **Fase 2 Pendiente**: Integración con autenticación JWT (16 pruebas)

**Próxima acción recomendada**: Instalar PyJWT y configurar OTHERS_KEY para habilitar las 16 pruebas de integración restantes.
