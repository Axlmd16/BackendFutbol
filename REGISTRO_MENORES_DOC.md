# Registro de Deportista Menor de Edad - Documentación

## 📋 Descripción
Este documento describe la funcionalidad de registro de deportistas menores de 18 años en la escuela de fútbol.

## 🎯 Endpoint
```
POST /api/v1/inscription/escuela-futbol/deportista-menor
```

## 🔒 Validaciones de Seguridad Implementadas (OWASP)

### 1. Validación de Edad
- El deportista debe ser menor de 18 años (basado en fecha de nacimiento)
- Edad mínima: 5 años
- Cálculo automático de edad considerando mes y día

### 2. Autorización Parental
- Campo obligatorio: `parental_authorization` debe ser `true`
- Validación a nivel de schema (Pydantic)
- Validación adicional en controlador (doble verificación)
- Rechaza el registro si no hay autorización expresa

### 3. Validación de Unicidad
- DNI del menor no puede existir previamente en la base de datos
- DNI del representante se verifica (puede reutilizarse si ya existe)
- Previene registros duplicados

### 4. Sanitización de Entradas
- **DNI**: Solo alfanuméricos y guiones (`^[A-Za-z0-9-]+$`)
- **Nombres**: Solo letras, espacios y caracteres latinos (`^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$`)
- **Teléfono**: Solo números, espacios, guiones, paréntesis y + (`^[0-9\s\-\(\)\+]+$`)
- **Email**: Validación EmailStr de Pydantic
- **Sexo**: Pattern estricto `^(M|F)$`

### 5. Prevención de Inyección SQL
- Uso de SQLAlchemy ORM (sin SQL raw)
- Parámetros bind automáticos
- Validación y sanitización en schemas

### 6. Manejo de Transacciones
- Operaciones atómicas con rollback automático en caso de error
- Log detallado de cada operación para auditoría

## 📝 Estructura del Request

### JSON de Ejemplo
```json
{
  "first_name": "Juan Carlos",
  "last_name": "Pérez López",
  "dni": "12345678",
  "birth_date": "2010-05-15",
  "sex": "M",
  "parental_authorization": true,
  "representative": {
    "first_name": "María Elena",
    "last_name": "López García",
    "dni": "87654321",
    "address": "Av. Principal 123, Ciudad, Ecuador",
    "phone": "+593 99 123 4567",
    "email": "maria.lopez@email.com"
  }
}
```

### Campos Requeridos

#### Deportista Menor
| Campo | Tipo | Validación | Descripción |
|-------|------|------------|-------------|
| `first_name` | string | 2-100 caracteres, solo letras | Nombres del deportista |
| `last_name` | string | 2-100 caracteres, solo letras | Apellidos del deportista |
| `dni` | string | 8-20 caracteres, alfanumérico | Documento de identidad |
| `birth_date` | date | YYYY-MM-DD, edad 5-17 años | Fecha de nacimiento |
| `sex` | string | "M" o "F" | Sexo del deportista |
| `parental_authorization` | boolean | Debe ser `true` | Autorización parental |

#### Representante Legal
| Campo | Tipo | Validación | Descripción |
|-------|------|------------|-------------|
| `first_name` | string | 2-100 caracteres, solo letras | Nombres del representante |
| `last_name` | string | 2-100 caracteres, solo letras | Apellidos del representante |
| `dni` | string | 8-20 caracteres, alfanumérico | Documento de identidad |
| `address` | string | 5-255 caracteres | Dirección completa |
| `phone` | string | 7-20 caracteres | Número de teléfono |
| `email` | string | Email válido | Correo electrónico |

## ✅ Respuesta Exitosa (201 Created)

```json
{
  "status": "success",
  "message": "Deportista menor de edad registrado exitosamente. El representante legal ha sido vinculado correctamente.",
  "data": {
    "athlete": {
      "id": 1,
      "first_name": "Juan Carlos",
      "last_name": "Pérez López",
      "dni": "12345678",
      "birth_date": "2010-05-15",
      "sex": "M",
      "type_athlete": "MINOR",
      "representative_id": 1,
      "parental_authorization": "SI",
      "created_at": "2025-12-08T10:30:00.000Z",
      "updated_at": null,
      "is_active": true
    },
    "representative": {
      "id": 1,
      "first_name": "María Elena",
      "last_name": "López García",
      "dni": "87654321",
      "address": "Av. Principal 123, Ciudad, Ecuador",
      "phone": "+593 99 123 4567",
      "email": "maria.lopez@email.com",
      "created_at": "2025-12-08T10:30:00.000Z",
      "updated_at": null,
      "is_active": true
    }
  },
  "errors": null
}
```

## ❌ Respuestas de Error

### Error 422: Sin Autorización Parental
```json
{
  "status": "error",
  "message": "Se requiere autorización parental explícita para registrar menores de edad. Por favor, asegúrese de obtener el consentimiento firmado del tutor legal.",
  "data": null,
  "errors": null
}
```

### Error 422: Mayor de Edad
```json
{
  "status": "error",
  "message": "El deportista debe ser menor de 18 años para este tipo de registro",
  "data": null,
  "errors": null
}
```

### Error 409: DNI Duplicado
```json
{
  "status": "error",
  "message": "Ya existe un deportista registrado con el DNI: 12345678",
  "data": null,
  "errors": null
}
```

### Error 422: Validación de Campos
```json
{
  "status": "error",
  "message": "Error de validación",
  "data": null,
  "errors": [
    {
      "field": "birth_date",
      "message": "El deportista debe ser menor de 18 años para usar este registro",
      "type": "value_error"
    }
  ]
}
```

## 🧪 Ejemplo de Prueba con cURL

```bash
curl -X POST "http://localhost:8000/api/v1/inscription/escuela-futbol/deportista-menor" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Juan Carlos",
    "last_name": "Pérez López",
    "dni": "12345678",
    "birth_date": "2010-05-15",
    "sex": "M",
    "parental_authorization": true,
    "representative": {
      "first_name": "María Elena",
      "last_name": "López García",
      "dni": "87654321",
      "address": "Av. Principal 123, Ciudad, Ecuador",
      "phone": "+593 99 123 4567",
      "email": "maria.lopez@email.com"
    }
  }'
```

## 🧪 Ejemplo de Prueba con Python

```python
import requests
import json

url = "http://localhost:8000/api/v1/inscription/escuela-futbol/deportista-menor"

payload = {
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
        "address": "Av. Principal 123, Ciudad, Ecuador",
        "phone": "+593 99 123 4567",
        "email": "maria.lopez@email.com"
    }
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(f"Status Code: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

## 🏗️ Arquitectura Implementada

### Capas del Sistema

1. **Router** (`inscription_router.py`)
   - Definición del endpoint POST
   - Manejo de excepciones HTTP
   - Formateo de respuestas estándar

2. **Controller** (`athlete_controller.py`)
   - Lógica de negocio
   - Validaciones adicionales
   - Orquestación de DAOs
   - Logging y auditoría

3. **DAO** (`athlete_dao.py`, `representative_dao.py`)
   - Operaciones de base de datos
   - Consultas especializadas
   - Manejo de transacciones

4. **Models** (`athlete.py`, `representative.py`)
   - Definición de tablas SQLAlchemy
   - Relaciones entre entidades
   - Campos de auditoría

5. **Schemas** (`athlete_schema.py`)
   - Validación de entrada (Pydantic)
   - Sanitización de datos
   - DTOs de respuesta

## 📊 Modelo de Datos

### Tabla: `athletes`
```sql
- id (PK, Integer, Auto)
- first_name (String 100)
- last_name (String 100)
- dni (String 20, Unique, Index)
- birth_date (Date, Nullable)
- sex (String 10, Nullable)
- type_athlete (String 50) -- "MINOR" para menores
- representative_id (FK -> representatives.id, Nullable)
- parental_authorization (String 10, Nullable) -- "SI" / "NO"
- created_at (DateTime)
- updated_at (DateTime)
- is_active (Boolean, Default: True)
```

### Tabla: `representatives`
```sql
- id (PK, Integer, Auto)
- first_name (String 100)
- last_name (String 100)
- dni (String 20, Unique, Index)
- address (String 255)
- phone (String 20)
- email (String 100)
- created_at (DateTime)
- updated_at (DateTime)
- is_active (Boolean, Default: True)
```

### Relación
- Un `Athlete` (menor) puede tener un `Representative`
- Un `Representative` puede tener múltiples `Athletes`
- Relación: One-to-Many (Representative -> Athletes)

## 📈 Logs de Auditoría

El sistema registra automáticamente:

```
✅ Deportista menor registrado exitosamente - 
   Atleta ID: 1, DNI: 12345678, 
   Representante ID: 1, DNI: 87654321, 
   Edad: 15 años
```

Eventos registrados:
- ✅ Registro exitoso con todos los detalles
- ⚠️ Intentos de registro sin autorización parental
- ⚠️ Intentos de registro de mayores de edad
- ⚠️ Intentos de DNI duplicado
- ❌ Errores de base de datos

## 🔐 Consideraciones de Seguridad

1. **OWASP A03:2021 - Injection**
   - ✅ Sanitización de todas las entradas
   - ✅ Uso de ORM (SQLAlchemy)
   - ✅ Validación de patrones regex

2. **OWASP A04:2021 - Insecure Design**
   - ✅ Validación de autorización parental obligatoria
   - ✅ Doble verificación de edad
   - ✅ Verificación de unicidad de DNI

3. **OWASP A09:2021 - Security Logging**
   - ✅ Logs detallados de cada operación
   - ✅ Registro de intentos fallidos
   - ✅ Auditoría completa

## 📚 Documentación Interactiva

Accede a la documentación interactiva en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Scalar**: http://localhost:8000/scalar

## 🎯 Casos de Uso

### Caso 1: Registro Normal Exitoso
- Menor de 5-17 años
- Autorización parental = true
- DNI único (no existe previamente)
- Resultado: ✅ 201 Created

### Caso 2: Representante Existente
- Menor nuevo
- Representante ya registrado con mismo DNI
- Resultado: ✅ 201 Created (reutiliza representante)

### Caso 3: Sin Autorización
- Menor válido
- Autorización parental = false
- Resultado: ❌ 422 Validation Error

### Caso 4: Mayor de Edad
- Fecha de nacimiento indica >= 18 años
- Resultado: ❌ 422 Validation Error

### Caso 5: DNI Duplicado
- Menor con DNI ya existente en DB
- Resultado: ❌ 409 Conflict

## 🛠️ Mantenimiento

### Modificar Validaciones
- Editar `app/schemas/athlete_schema.py`
- Validators personalizados en cada campo

### Agregar Campos
1. Actualizar modelo en `app/models/athlete.py` o `representative.py`
2. Actualizar schema en `app/schemas/athlete_schema.py`
3. Ejecutar migración de base de datos

### Cambiar Lógica de Negocio
- Editar `app/controllers/athlete_controller.py`
- Método `register_minor_athlete()`
