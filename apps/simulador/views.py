import json

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.evaluacion.models import IntentoSimulacion, RegistroActuacion
from apps.usuarios.permissions import estudiante_required
from .models import CasoForense


def _leer_json(request):
    try:
        datos = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


@require_POST
@estudiante_required
def iniciar_intento(request, caso_id):
    """Inicia un intento nuevo, conservando el historial de intentos anteriores."""
    caso = get_object_or_404(CasoForense, pk=caso_id, activo=True)
    with transaction.atomic():
        # Bloquear al estudiante evita que dos peticiones concurrentes usen el mismo número.
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        numero = IntentoSimulacion.siguiente_numero(request.user, caso)
        intento = IntentoSimulacion.objects.create(
            estudiante=request.user,
            caso_forense=caso,
            numero_intento=numero,
        )
    return JsonResponse({
        "ok": True,
        "mensaje": "El intento de simulación se inició correctamente.",
        "intento_id": intento.pk,
        "numero_intento": intento.numero_intento,
        "estado": intento.estado,
        "url": f"/simulador/intentos/{intento.pk}/",
    }, status=201)


@require_GET
@estudiante_required
def lista_casos(request):
    casos = CasoForense.objects.filter(activo=True).select_related("tema_teorico").order_by("titulo")
    return render(request, "simulador/lista_casos.html", {"casos": casos})


@require_GET
@estudiante_required
def ver_intento(request, intento_id):
    intento = get_object_or_404(IntentoSimulacion, pk=intento_id, estudiante=request.user)
    actuaciones = intento.actuaciones.order_by("timestamp", "id")
    return render(request, "simulador/intento.html", {"intento": intento, "actuaciones": actuaciones})


@require_GET
@estudiante_required
def descargar_evidencia(request, intento_id):
    """Entrega el archivo de evidencia del caso y deja constancia de la descarga."""
    with transaction.atomic():
        intento = get_object_or_404(
            IntentoSimulacion.objects.select_for_update(), pk=intento_id, estudiante=request.user
        )
        if intento.estado != IntentoSimulacion.Estado.EN_PROGRESO:
            return JsonResponse({"ok": False, "mensaje": "El intento ya está cerrado."}, status=409)
        evidencia = intento.caso_forense.archivo_evidencia
        if not evidencia:
            return JsonResponse({"ok": False, "mensaje": "Este caso no tiene un archivo de evidencia."}, status=404)
        RegistroActuacion.objects.create(
            intento=intento,
            tipo_accion=RegistroActuacion.TipoAccion.DESCARGA_EVIDENCIA,
            detalle="Descarga del archivo original de evidencia para la práctica.",
            es_correcta=True,
        )
        archivo = evidencia.open("rb")
        nombre = evidencia.name.rsplit("/", 1)[-1]
    respuesta = FileResponse(archivo, as_attachment=True, filename=nombre, content_type="application/octet-stream")
    return respuesta


@require_POST
@estudiante_required
def registrar_accion(request):
    """Registra la acción incluso si infringe el procedimiento para dejar auditoría."""
    datos = _leer_json(request)
    if datos is None:
        return JsonResponse({"ok": False, "mensaje": "El cuerpo debe ser un objeto JSON válido."}, status=400)
    try:
        intento_id = int(datos.get("intento_id"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "mensaje": "Debes indicar un intento_id válido."}, status=400)

    accion_recibida = str(datos.get("tipo_accion", datos.get("accion", ""))).strip().upper()
    tipos_validos = RegistroActuacion.TipoAccion.values
    accion_valida = accion_recibida in tipos_validos and accion_recibida != RegistroActuacion.TipoAccion.OTRA
    tipo_accion = accion_recibida if accion_valida else RegistroActuacion.TipoAccion.OTRA
    detalle = str(datos.get("detalle", "")).strip()[:4000]
    objetivo = str(datos.get("objetivo", "COPIA_TRABAJO")).strip().upper()
    analisis = {
        RegistroActuacion.TipoAccion.VERIFICACION_HASH,
        RegistroActuacion.TipoAccion.INSPECCION_LOGS,
        RegistroActuacion.TipoAccion.IDENTIFICACION_INDICIO,
        RegistroActuacion.TipoAccion.EXTRACCION_METADATOS,
    }

    with transaction.atomic():
        intento = get_object_or_404(
            IntentoSimulacion.objects.select_for_update(), pk=intento_id, estudiante=request.user
        )
        if intento.estado != IntentoSimulacion.Estado.EN_PROGRESO:
            return JsonResponse({"ok": False, "mensaje": "El intento ya está cerrado."}, status=409)

        es_correcta = accion_valida
        retroalimentacion = "Acción registrada correctamente."
        if not accion_valida:
            es_correcta = False
            retroalimentacion = "La acción indicada no existe; se dejó registrada para auditoría."
        elif tipo_accion == RegistroActuacion.TipoAccion.CREACION_COPIA_TRABAJO:
            if intento.copia_trabajo_creada:
                es_correcta = False
                retroalimentacion = "La copia de trabajo ya fue creada para este intento."
            else:
                intento.copia_trabajo_creada = True
                intento.copia_trabajo_creada_en = timezone.now()
                intento.save(update_fields=["copia_trabajo_creada", "copia_trabajo_creada_en"])
                retroalimentacion = "Copia de trabajo virtual creada. Ya puedes analizar esa copia."
        elif tipo_accion in analisis:
            if not intento.copia_trabajo_creada:
                es_correcta = False
                retroalimentacion = "Falta procedimental: crea una copia de trabajo antes de analizar la evidencia."
            elif objetivo == "ORIGINAL":
                es_correcta = False
                retroalimentacion = "Falta procedimental: realiza el análisis sobre la copia de trabajo, no sobre el original."
            elif objetivo != "COPIA_TRABAJO":
                es_correcta = False
                retroalimentacion = "Indica COPIA_TRABAJO como objetivo del análisis."

        RegistroActuacion.objects.create(
            intento=intento,
            tipo_accion=tipo_accion,
            detalle=detalle or retroalimentacion,
            es_correcta=es_correcta,
        )

    return JsonResponse({
        "ok": True,
        "mensaje": retroalimentacion,
        "procedimentalmente_correcta": es_correcta,
        "tipo_accion": tipo_accion,
    })


@require_GET
@estudiante_required
def obtener_caso_intento(request, intento_id):
    """Devuelve la información didáctica y los registros sintéticos del intento propio."""
    intento = get_object_or_404(IntentoSimulacion, pk=intento_id, estudiante=request.user)
    caso = intento.caso_forense
    return JsonResponse({
        "ok": True,
        "caso": {
            "titulo": caso.titulo,
            "descripcion_escenario": caso.descripcion_escenario,
            "dificultad": caso.dificultad,
            "registro_actividad": caso.registro_actividad,
            "copia_trabajo_creada": intento.copia_trabajo_creada,
        },
    })
