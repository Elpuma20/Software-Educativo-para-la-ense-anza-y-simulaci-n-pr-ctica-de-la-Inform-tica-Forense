import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.usuarios.permissions import docente_required, estudiante_required
from .models import CadenaCustodia, IntentoSimulacion


def _leer_json(request):
    try:
        datos = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def _fecha_hora(valor):
    if not isinstance(valor, str):
        raise ValueError("La fecha y hora de recolección deben estar en formato ISO 8601.")
    try:
        fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("La fecha y hora de recolección no tienen un formato válido.") from exc
    if timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())
    return fecha


@require_POST
@estudiante_required
def finalizar_intento(request, intento_id):
    """Guarda la cadena de custodia y cierra el intento con una nota procedimental."""
    datos = _leer_json(request)
    if datos is None:
        return JsonResponse({"ok": False, "mensaje": "El cuerpo debe ser un objeto JSON válido."}, status=400)
    custodia = datos.get("cadena_custodia", datos)
    if not isinstance(custodia, dict):
        return JsonResponse({"ok": False, "mensaje": "cadena_custodia debe ser un objeto JSON."}, status=400)

    campos = (
        "identificador_evidencia", "descripcion", "hash_registrado",
        "fecha_hora_recoleccion", "origen", "destino_transferencia", "proposito_traslado",
    )
    faltantes = [campo for campo in campos if not str(custodia.get(campo, "")).strip()]
    if faltantes:
        return JsonResponse({"ok": False, "mensaje": "Completa todos los campos obligatorios de la cadena de custodia.", "campos_faltantes": faltantes}, status=400)
    hash_registrado = str(custodia["hash_registrado"]).strip()
    if len(hash_registrado) != 64 or any(caracter not in "0123456789abcdefABCDEF" for caracter in hash_registrado):
        return JsonResponse({"ok": False, "mensaje": "El hash registrado debe tener 64 caracteres hexadecimales."}, status=400)
    try:
        fecha_recoleccion = _fecha_hora(custodia["fecha_hora_recoleccion"])
    except ValueError as error:
        return JsonResponse({"ok": False, "mensaje": str(error)}, status=400)

    with transaction.atomic():
        intento = get_object_or_404(
            IntentoSimulacion.objects.select_for_update(), pk=intento_id, estudiante=request.user
        )
        if intento.estado != IntentoSimulacion.Estado.EN_PROGRESO:
            return JsonResponse({"ok": False, "mensaje": "El intento ya está cerrado."}, status=409)
        if not intento.copia_trabajo_creada:
            return JsonResponse({
                "ok": False,
                "mensaje": "Crea una copia de trabajo antes de finalizar la práctica.",
            }, status=400)

        CadenaCustodia.objects.update_or_create(
            intento=intento,
            defaults={
                "identificador_evidencia": str(custodia["identificador_evidencia"]).strip()[:120],
                "descripcion": str(custodia["descripcion"]).strip(),
                "hash_registrado": hash_registrado.lower(),
                "fecha_hora_recoleccion": fecha_recoleccion,
                "origen": str(custodia["origen"]).strip()[:240],
                "destino_transferencia": str(custodia["destino_transferencia"]).strip()[:240],
                "proposito_traslado": str(custodia["proposito_traslado"]).strip(),
                "observaciones": str(custodia.get("observaciones", "")).strip(),
            },
        )
        total = intento.actuaciones.count()
        correctas = intento.actuaciones.filter(es_correcta=True).count()
        puntaje = (Decimal(correctas) * Decimal("100") / Decimal(total)).quantize(Decimal("0.01")) if total else Decimal("0.00")
        intento.estado = IntentoSimulacion.Estado.COMPLETADO
        intento.puntaje_automatico = puntaje
        intento.cerrado_en = timezone.now()
        intento.save(update_fields=["estado", "puntaje_automatico", "cerrado_en"])

    return JsonResponse({
        "ok": True,
        "mensaje": "La cadena de custodia se guardó y el intento fue finalizado.",
        "estado": intento.estado,
        "puntaje_automatico": str(puntaje),
        "actuaciones_correctas": correctas,
        "actuaciones_totales": total,
    })


@require_GET
@docente_required
def revisar_intento(request, intento_id):
    """Presenta al docente el intento y su línea de tiempo de actuaciones."""
    intento = get_object_or_404(IntentoSimulacion.objects.select_related("estudiante", "caso_forense"), pk=intento_id)
    actuaciones = intento.actuaciones.order_by("timestamp", "id").values(
        "tipo_accion", "detalle", "es_correcta", "timestamp"
    )
    try:
        cadena = intento.cadena_custodia
    except CadenaCustodia.DoesNotExist:
        cadena = None
    return JsonResponse({
        "ok": True,
        "intento": {
            "id": intento.pk,
            "estudiante": intento.estudiante.username,
            "caso": intento.caso_forense.titulo,
            "numero_intento": intento.numero_intento,
            "estado": intento.estado,
            "puntaje_automatico": str(intento.puntaje_automatico),
            "puntaje_docente": str(intento.puntaje_docente) if intento.puntaje_docente is not None else None,
            "retroalimentacion": intento.retroalimentacion,
            "actuaciones": list(actuaciones),
            "cadena_custodia": {
                "identificador_evidencia": cadena.identificador_evidencia,
                "descripcion": cadena.descripcion,
                "hash_registrado": cadena.hash_registrado,
                "fecha_hora_recoleccion": cadena.fecha_hora_recoleccion,
                "origen": cadena.origen,
                "destino_transferencia": cadena.destino_transferencia,
                "proposito_traslado": cadena.proposito_traslado,
                "observaciones": cadena.observaciones,
            } if cadena else None,
        },
    })


@require_GET
@estudiante_required
def ver_resultado(request, intento_id):
    intento = get_object_or_404(IntentoSimulacion, pk=intento_id, estudiante=request.user)
    if intento.estado != IntentoSimulacion.Estado.COMPLETADO:
        return JsonResponse({"ok": False, "mensaje": "El intento aún está en progreso."}, status=409)
    return JsonResponse({
        "ok": True,
        "estado": intento.estado,
        "puntaje_automatico": str(intento.puntaje_automatico),
        "puntaje_docente": str(intento.puntaje_docente) if intento.puntaje_docente is not None else None,
        "retroalimentacion": intento.retroalimentacion,
    })


@require_POST
@docente_required
def calificar_intento(request, intento_id):
    """Permite a un docente aprobado asignar nota y retroalimentación."""
    datos = _leer_json(request)
    if datos is None:
        return JsonResponse({"ok": False, "mensaje": "El cuerpo debe ser un objeto JSON válido."}, status=400)
    try:
        puntaje = Decimal(str(datos["puntaje_docente"]))
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return JsonResponse({"ok": False, "mensaje": "Indica un puntaje docente numérico entre 0 y 100."}, status=400)
    if not puntaje.is_finite() or puntaje < 0 or puntaje > 100:
        return JsonResponse({"ok": False, "mensaje": "El puntaje docente debe estar entre 0 y 100."}, status=400)

    intento = get_object_or_404(IntentoSimulacion, pk=intento_id)
    intento.puntaje_docente = puntaje.quantize(Decimal("0.01"))
    intento.retroalimentacion = str(datos.get("retroalimentacion", "")).strip()
    intento.save(update_fields=["puntaje_docente", "retroalimentacion"])
    return JsonResponse({"ok": True, "mensaje": "La evaluación docente fue guardada.", "puntaje_docente": str(intento.puntaje_docente)})
