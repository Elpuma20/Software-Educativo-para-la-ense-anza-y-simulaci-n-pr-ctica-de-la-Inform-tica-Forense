from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


def _es_api(request):
    return request.path.startswith("/api/") or "application/json" in request.headers.get("Accept", "")


def _respuesta_no_autorizada(request, mensaje, status):
    if _es_api(request):
        return JsonResponse({"ok": False, "mensaje": mensaje}, status=status)
    if status == 401:
        return redirect_to_login(request.get_full_path())
    raise PermissionDenied(mensaje)


def _requiere_rol(comprobacion, mensaje):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = request.user
            if not usuario.is_authenticated:
                return _respuesta_no_autorizada(request, "Debes iniciar sesión para continuar.", 401)
            if not comprobacion(usuario):
                return _respuesta_no_autorizada(request, mensaje, 403)
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


docente_required = _requiere_rol(
    lambda usuario: usuario.is_superuser or getattr(usuario, "es_docente_aprobado", False),
    "No tienes permisos de docente aprobado.",
)
estudiante_required = _requiere_rol(
    lambda usuario: getattr(usuario, "es_estudiante", False),
    "Esta acción está disponible únicamente para estudiantes.",
)
