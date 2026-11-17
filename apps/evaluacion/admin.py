from django.contrib import admin

from .models import CadenaCustodia, IntentoSimulacion, RegistroActuacion


class RegistroActuacionEnLinea(admin.TabularInline):
    model = RegistroActuacion
    extra = 0
    can_delete = False
    readonly_fields = ("tipo_accion", "detalle", "es_correcta", "timestamp")


@admin.register(IntentoSimulacion)
class IntentoSimulacionAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "caso_forense", "numero_intento", "estado", "puntaje_automatico", "puntaje_docente", "iniciado_en")
    list_filter = ("estado", "caso_forense")
    search_fields = ("estudiante__username", "estudiante__cedula", "caso_forense__titulo")
    readonly_fields = ("iniciado_en", "cerrado_en", "copia_trabajo_creada_en")
    inlines = (RegistroActuacionEnLinea,)


@admin.register(CadenaCustodia)
class CadenaCustodiaAdmin(admin.ModelAdmin):
    list_display = ("intento", "identificador_evidencia", "fecha_hora_recoleccion", "actualizado_en")
    search_fields = ("identificador_evidencia", "intento__estudiante__username")
