# Software educativo de informática forense

Backend modular en Python 3.11+ y Django 5.x para prácticas universitarias con evidencia sintética. Utiliza PostgreSQL, Django Templates y endpoints JSON protegidos por sesión y CSRF.

## Estructura

```text
config/                 Configuración, rutas y servidores ASGI/WSGI
apps/
  usuarios/             Usuario personalizado, roles y permisos
  contenidos/           Temas teóricos
  simulador/             Casos, descargas y controles del simulador
  evaluacion/            Intentos, actuaciones, custodia y evaluación
```

## Preparar el entorno local

Requiere Python 3.11 o superior y Docker Compose (o una instalación local de PostgreSQL).

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env               # Windows PowerShell: Copy-Item .env.example .env
docker compose up -d postgres
python manage.py migrate
python manage.py cargar_caso_piloto
python manage.py runserver
```

Abre `http://127.0.0.1:8000/cuentas/login/` e inicia sesión con una de las cuentas que el comando de piloto imprimió. Las contraseñas iniciales aleatorias se muestran solo al crear cada cuenta; el comando no las restablece en ejecuciones posteriores.

El docente piloto queda aprobado y puede entrar en `/admin/` para crear o editar temas y casos, consultar intentos y actuaciones, auditar cadenas de custodia y calificar. Para la cuenta administradora, crea un superusuario con `python manage.py createsuperuser`.

## Flujo del estudiante

1. Iniciar un intento con `POST /simulador/casos/<id>/intentos/iniciar/`.
2. Descargar la evidencia del intento con `GET /simulador/intentos/<id>/evidencia/`.
3. Crear la copia de trabajo mediante la actuación `CREACION_COPIA_TRABAJO`.
4. Registrar las verificaciones y demás análisis en la copia.
5. Finalizar enviando la cadena de custodia a `POST /api/evaluacion/intentos/<id>/finalizar/`.
6. Consultar el resultado en `GET /api/evaluacion/intentos/<id>/resultado/`.

Para recorrer el flujo desde las pantallas incluidas, inicia sesión y abre `/simulador/casos/`. La pantalla del intento permite descargar la evidencia, registrar actuaciones y completar la cadena de custodia.

### Registrar una actuación

`POST /api/simulador/registrar-accion/` recibe JSON. El navegador debe enviar la cookie de sesión y la cabecera `X-CSRFToken`.

```json
{
  "intento_id": 1,
  "tipo_accion": "VERIFICACION_HASH",
  "objetivo": "COPIA_TRABAJO",
  "detalle": "Hash SHA-256 calculado sobre la copia recibida"
}
```

Las acciones de análisis se registran como procedimentalmente incorrectas si aún no se creó una copia o si apuntan al original. El evento incorrecto se conserva en la auditoría y la respuesta incluye `procedimentalmente_correcta: false`.

### Finalizar y documentar custodia

`POST /api/evaluacion/intentos/<id>/finalizar/` acepta:

```json
{
  "cadena_custodia": {
    "identificador_evidencia": "LAB-IMG-001",
    "descripcion": "Archivo sintético recibido para práctica académica",
    "hash_registrado": "<64 caracteres hexadecimales>",
    "fecha_hora_recoleccion": "2026-11-17T10:30:00-04:00",
    "origen": "Laboratorio universitario",
    "destino_transferencia": "Estación de análisis 01",
    "proposito_traslado": "Análisis en copia de trabajo",
    "observaciones": "Sello de evidencia intacto"
  }
}
```

La nota automática inicial es el porcentaje de actuaciones correctas. La nota y la retroalimentación docente se guardan por separado. Las actuaciones son de solo anexado durante un intento abierto; las infracciones procedimentales quedan registradas.

## Roles y protección

- Los permisos de `estudiante_required` y `docente_required` restringen las vistas.
- Tras `migrate`, se crea el grupo `Docentes aprobados` con permisos mínimos para editar contenidos/casos y consultar evaluaciones. Aprobar a un docente en `/admin/` le habilita el acceso al panel; revocar la aprobación lo retira del grupo.
- Django Admin queda reservado a cuentas de staff. Los superusuarios conservan control total.
- En producción, configura una `SECRET_KEY` propia, credenciales PostgreSQL seguras, `DEBUG=False`, `ALLOWED_HOSTS`, HTTPS y un almacenamiento privado para evidencias.
