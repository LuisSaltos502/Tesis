Tesis Back API - README


comando para activar el entorno virtual en windows: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\tesis_back\venv\Scripts\activate


Descripcion
API del backend del proyecto de tesis. Implementada con FastAPI.

Inicio rapido
- Crear un entorno virtual dentro de esta carpeta (`tesis_back`):
  cd tesis_back
  python -m venv venv
- Activar el entorno virtual (PowerShell):
  .\venv\Scripts\activate
- Si PowerShell bloquea el script de activacion:
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
- Crear el archivo de entorno en `app/.env`.
- Instalar dependencias:
  pip install -r requirements.txt
- Ejecutar la app con Uvicorn:
  uvicorn main:app --reload

Dependencias y versiones
- `requirements.txt` contiene las versiones exactas del entorno virtual (congeladas).
- Para actualizarlo en este mismo entorno:
  pip freeze > requirements.txt

Base URL
- Por defecto: http://localhost:8000
- Documentacion interactiva: /docs y /redoc

Autenticacion
- Usa JWT en el header: Authorization: Bearer <token>
- Obtener token (JSON): POST /auth/login
  Body:
    {
      "correo": "user@example.com",
      "password": "secret"
    }
- Obtener token (OAuth2 form): POST /auth/token
  Form:
    username=<correo>
    password=<password>
- Perfil actual: GET /auth/me

Roles
- UserRole: admin | usuario | operador
- DeviceRole: prototipo_esp32 | raspberry_pi_gateway
- OrigenRole: simulado | fisico

Variables de entorno requeridas (app/.env)
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
- SECRET_KEY, Access_Token_Expire_Minutes_Usuarios, Access_Token_Expire_Minutes_Operadores, Algorithm
- PH_MIN, PH_MAX, TURB_MAX, TDS_MAX, ALERT_COOLDOWN_MINUTES

Endpoints
SYSTEM
- GET /system/db-check
  Requiere auth (admin, usuario, operador).

AUTH
- POST /auth/login
  Body JSON: correo, password
- POST /auth/token
  Body form: username, password
- GET /auth/me
  Requiere auth.

USUARIOS
- POST /usuarios
  Crea usuario. Body JSON: nombre, segundo_nombre?, apellido, segundo_apellido?, correo, celular?, password, rol
- GET /usuarios/{user_id}
  Requiere role admin u operador.
- GET /usuarios
  Query: skip=0, limit=50, solo_activos=true
  Requiere role admin u operador.
- PATCH /usuarios/{user_id}
  Requiere auth. Usuario solo puede actualizar sus propios datos.
- DELETE /usuarios/{user_id}
  Requiere auth. Usuario solo puede desactivar su propia cuenta.
- PATCH /usuarios/me/password
  Body JSON: current_password, new_password

DISPOSITIVOS
- POST /dispositivos
  Requiere auth.
  Usuario crea para si mismo. Admin/operador puede setear id_usuario.
  Body JSON: nombre, mac, rol_dispositivo, origen, id_usuario?, ubicacion_texto?, latitud?, longitud?
- GET /dispositivos/{mac}
  Requiere role admin, usuario u operador.
- GET /dispositivos
  Query: skip=0, limit=50
  Requiere auth. Usuario ve solo sus dispositivos.
- PATCH /dispositivos/{mac}
  Requiere role admin, usuario u operador.
  Body JSON con campos opcionales.
- DELETE /dispositivos/{mac}
  Requiere role admin u operador.

Notas
- Los endpoints de listado soportan paginacion por skip/limit.
- El dispositivo retorna device_key y timestamps en lectura.
