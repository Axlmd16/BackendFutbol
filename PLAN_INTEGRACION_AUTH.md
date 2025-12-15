# 🔐 PLAN DE INTEGRACIÓN Y PRUEBAS: Spring Boot Auth + FastAPI

## 📊 RESUMEN EJECUTIVO

### ⚠️ PROBLEMAS DETECTADOS

1. **CRÍTICO - Endpoints sin protección**
   - ❌ `/inscription/deportista-menor` estaba completamente abierto
   - ❌ No había validación de tokens JWT
   - ❌ Faltaba sistema de inyección de dependencias de seguridad

2. **CRÍTICO - Clave secreta faltante**
   - ❌ `OTHERS_KEY` del servicio Spring Boot no estaba en FastAPI
   - ❌ Sin esta clave, imposible validar tokens firmados por Java

3. **ADVERTENCIA - Posible incompatibilidad de algoritmos**
   - ⚠️ Spring Boot puede usar HS512 o RS256
   - ⚠️ FastAPI estaba configurado para HS256
   - ⚠️ Requiere validación manual del algoritmo exacto

### ✅ SOLUCIONES IMPLEMENTADAS

1. **Módulo de seguridad completo** (`app/core/security.py`)
   - ✅ Validación de tokens JWT
   - ✅ Extracción de información de usuario
   - ✅ Inyección de dependencias `get_current_user`
   - ✅ Soporte multi-algoritmo (HS256, HS512)

2. **Configuración actualizada** (`app/core/config.py`)
   - ✅ Agregada variable `OTHERS_KEY`
   - ✅ Sincronizada con el servicio Spring Boot

3. **Endpoint protegido** (`inscription_router.py`)
   - ✅ Agregada dependencia `Depends(get_current_user)`
   - ✅ Auditoría de quién registra menores
   - ✅ Documentación de seguridad en OpenAPI

---

## 🏗️ ARQUITECTURA DE INTEGRACIÓN

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTE (Frontend)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ 1. Login
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Spring Boot (Puerto 8096)                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │ POST /api/person/login                             │     │
│  │ Body: {"email": "...", "password": "..."}          │     │
│  │ Response: {"data": {"token": "Bearer eyJ..."}}     │     │
│  │                                                     │     │
│  │ Firma token con: OTHERS_KEY=1234567FDUCAMETB       │     │
│  │ Algoritmo: HS512 o HS256 (a confirmar)            │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ 2. Token firmado
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         FastAPI (Puerto 8000)                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │ POST /api/v1/inscription/deportista-menor          │     │
│  │ Header: Authorization: Bearer eyJ...               │     │
│  │                                                     │     │
│  │ 1. HTTPBearer extrae token                         │     │
│  │ 2. get_current_user() valida con OTHERS_KEY        │     │
│  │ 3. Decodifica y extrae usuario                     │     │
│  │ 4. Ejecuta lógica de negocio                       │     │
│  │ 5. Registra auditoría (quién lo hizo)             │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 PLAN DE EJECUCIÓN

### PASO 1: Actualizar Variables de Entorno

Agregar a tu archivo `.env`:

```bash
# ================= SECURITY (SPRING BOOT INTEGRATION) =================
# Clave compartida con Spring Boot para validar tokens
OTHERS_KEY=1234567FDUCAMETB
```

**CRÍTICO:** Esta clave DEBE coincidir exactamente con el valor en `docker-compose.yml`

### PASO 2: Instalar Dependencias

```bash
# Si no tienes PyJWT instalado
pip install pyjwt[crypto]

# O con uv (si lo usas)
uv pip install pyjwt[crypto]
```

### PASO 3: Levantar Infraestructura

```bash
# Levantar servicios Docker (Spring Boot + MariaDB)
docker-compose up -d

# Verificar que los servicios estén corriendo
docker-compose ps

# Ver logs del servicio Spring Boot
docker logs -f springboot-app

# Esperar a que Spring Boot esté listo (buscar: "Started Application")
```

### PASO 4: Verificar Endpoint de Login Spring Boot

**INVESTIGACIÓN NECESARIA:** Necesitas confirmar la ruta exacta de login.

Opciones comunes en Spring Boot:
- `/api/person/login` (basado en tu código de PersonClient)
- `/auth/login`
- `/api/auth/login`
- `/login`

**Prueba manual:**

```bash
# Probar login en Spring Boot
curl -X POST http://localhost:8096/api/person/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@admin.com",
    "password": "12345678"
  }'

# Respuesta esperada:
{
  "data": {
    "token": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJhZG1pbkBhZG1pbi5jb20iLCJpYXQiOjE3MDI...",
    "user": { ... }
  }
}
```

### PASO 5: Levantar FastAPI

```bash
# Activar entorno virtual
source .venv/bin/activate  # Mac/Linux
# o
.venv\Scripts\activate  # Windows

# Ejecutar FastAPI
python main.py

# O con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 PLAN DE PRUEBAS MANUAL

### TEST 1: Obtener Token de Spring Boot

```bash
# PASO 1: Login en Spring Boot
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8096/api/person/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@admin.com",
    "password": "12345678"
  }')

echo "Respuesta completa:"
echo $TOKEN_RESPONSE | jq .

# PASO 2: Extraer solo el token
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.data.token')
echo "\nToken extraído:"
echo $TOKEN
```

**⚠️ NOTA:** Si el token ya viene con prefijo "Bearer", úsalo tal cual. Si no, agrégalo manualmente.

### TEST 2: Probar Endpoint Protegido de Ejemplo

```bash
# Probar endpoint de ejemplo (verifica que la autenticación funciona)
curl -X GET http://localhost:8000/api/v1/protected-example/basic-protected \
  -H "Authorization: $TOKEN"

# Respuesta esperada (si funciona):
{
  "status": "success",
  "message": "Bienvenido admin@admin.com",
  "data": {
    "user_id": 1,
    "email": "admin@admin.com",
    "role": "ADMIN",
    "external_id": "..."
  }
}

# Si falla con 401:
# - El token está mal formado
# - La clave OTHERS_KEY no coincide
# - El algoritmo de firma es diferente
```

### TEST 3: Registrar Deportista Menor (Endpoint Real)

```bash
# Crear archivo con datos de prueba
cat > minor_athlete_test.json <<'EOF'
{
  "first_name": "Juan Carlos",
  "last_name": "Pérez López",
  "dni": "TEST123456",
  "birth_date": "2010-05-15",
  "sex": "M",
  "parental_authorization": true,
  "representative": {
    "first_name": "María Elena",
    "last_name": "López García",
    "dni": "REP987654",
    "address": "Av. Principal 123, Ciudad, Ecuador",
    "phone": "+593 99 123 4567",
    "email": "maria.test@email.com"
  }
}
EOF

# Ejecutar registro con autenticación
curl -X POST http://localhost:8000/api/v1/inscription/escuela-futbol/deportista-menor \
  -H "Content-Type: application/json" \
  -H "Authorization: $TOKEN" \
  -d @minor_athlete_test.json | jq .

# Respuesta esperada (éxito):
{
  "status": "success",
  "message": "Deportista menor de edad registrado exitosamente...",
  "data": {
    "athlete": { ... },
    "representative": { ... }
  }
}
```

### TEST 4: Intentar Acceso SIN Token (Debe Fallar)

```bash
# Intentar sin token - debe retornar 401
curl -X POST http://localhost:8000/api/v1/inscription/escuela-futbol/deportista-menor \
  -H "Content-Type: application/json" \
  -d @minor_athlete_test.json

# Respuesta esperada:
{
  "detail": "Not authenticated"
}
```

### TEST 5: Token Inválido (Debe Fallar)

```bash
# Token falso
curl -X POST http://localhost:8000/api/v1/inscription/escuela-futbol/deportista-menor \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token_falso_123" \
  -d @minor_athlete_test.json

# Respuesta esperada:
{
  "detail": "Token inválido o corrupto"
}
```

---

## 🐛 TROUBLESHOOTING

### Problema 1: "Token inválido" con token válido

**Causa probable:** Algoritmo de firma incorrecto

**Solución:**
1. Inspeccionar el token JWT en [jwt.io](https://jwt.io)
2. Ver qué algoritmo usa (header "alg")
3. Actualizar `app/core/security.py` línea 66:

```python
# Si Spring Boot usa RS256 (clave pública/privada):
algorithms=["RS256"]

# Si usa HS512:
algorithms=["HS512"]

# Si no estás seguro, permitir ambos:
algorithms=["HS256", "HS512", "RS256"]
```

### Problema 2: "Token expirado" inmediatamente

**Causa probable:** Diferencia de zona horaria o reloj desincronizado

**Solución:**
```python
# En security.py, agregar opciones de leeway:
payload = jwt.decode(
    token,
    secret_key,
    algorithms=["HS256", "HS512"],
    options={
        "verify_signature": True,
        "verify_exp": True,
    },
    leeway=10  # 10 segundos de tolerancia
)
```

### Problema 3: Campos del payload no coinciden

**Causa:** La estructura del token de Spring Boot es diferente

**Solución:** Inspeccionar token real y ajustar `get_current_user()`:

```bash
# Decodificar token en la terminal
echo "eyJhbGc..." | cut -d'.' -f2 | base64 -d | jq .

# Ver qué campos contiene realmente, por ejemplo:
{
  "sub": "admin@admin.com",
  "userId": 1,
  "role": "ADMIN",
  "iat": 1702...,
  "exp": 1702...
}
```

Luego actualizar líneas 93-107 de `security.py` para usar los campos correctos.

### Problema 4: Spring Boot no inicia

```bash
# Ver logs
docker logs springboot-app

# Verificar salud de MariaDB
docker exec -it mariadb-db mysql -u desarrollo -pdesarrollo -e "SELECT 1"

# Reiniciar servicios
docker-compose restart
```

---

## 📋 CHECKLIST DE VALIDACIÓN

### Pre-Deploy

- [ ] `OTHERS_KEY` agregada al `.env`
- [ ] `PyJWT` instalado (`pip list | grep -i jwt`)
- [ ] `app/core/security.py` creado
- [ ] `inscription_router.py` actualizado con `Depends(get_current_user)`
- [ ] Docker compose funcionando (`docker-compose ps`)

### Pruebas Funcionales

- [ ] Login en Spring Boot retorna token
- [ ] Token puede ser decodificado en jwt.io
- [ ] Endpoint `/protected-example/basic-protected` funciona
- [ ] Endpoint `/inscription/deportista-menor` requiere autenticación
- [ ] Registro de menor exitoso con token válido
- [ ] Rechazo con 401 sin token
- [ ] Logs de auditoría muestran quién hizo el registro

### Pruebas de Seguridad

- [ ] Token expirado es rechazado
- [ ] Token malformado es rechazado
- [ ] Token con firma incorrecta es rechazado
- [ ] Headers de error incluyen `WWW-Authenticate: Bearer`

---

## 🎯 PRÓXIMOS PASOS (Opcional)

### Mejoras Recomendadas

1. **Cache de validación de tokens**
   - Usar Redis para cachear tokens validados
   - Reducir llamadas de decodificación

2. **Renovación automática de tokens**
   - Interceptor que renueva tokens cerca de expirar
   - Evitar interrupciones de sesión

3. **Roles y permisos granulares**
   - Implementar `require_role()` en más endpoints
   - Control de acceso basado en roles (RBAC)

4. **Rate limiting por usuario**
   - Limitar requests por token
   - Prevenir abuso de API

---

## 📞 CONTACTO Y SOPORTE

Si encuentras problemas:

1. **Revisar logs de FastAPI**: `tail -f logs/app.log`
2. **Revisar logs de Spring Boot**: `docker logs -f springboot-app`
3. **Validar token en jwt.io**: Copiar token y verificar estructura
4. **Ejecutar tests unitarios**: `pytest tests/test_security.py`

---

## 📚 REFERENCIAS

- [JWT.io - Token Debugger](https://jwt.io)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Spring Boot JWT Guide](https://spring.io/guides/gs/securing-web/)

---

**Última actualización:** 14 de diciembre de 2025
**Autor:** Copilot AI - Arquitecto de Software
**Estado:** ✅ Listo para pruebas
