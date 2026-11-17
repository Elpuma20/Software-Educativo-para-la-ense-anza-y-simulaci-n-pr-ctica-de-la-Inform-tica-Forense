from django.conf import settings
from django.db import models
from django.utils import timezone


class IntentoSimulacion(models.Model):
    class Estado(models.TextChoices):
        EN_PROGRESO = "EN_PROGRESO", "En progreso"
        COMPLETADO = "COMPLETADO", "Completado"

    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="intentos_simulacion")
    caso_forense = models.ForeignKey("simulador.CasoForense", on_delete=models.PROTECT, related_name="intentos")
    numero_intento = models.PositiveIntegerField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.EN_PROGRESO, db_index=True)
    puntaje_automatico = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    puntaje_docente = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    retroalimentacion = models.TextField(blank=True)
    iniciado_en = models.DateTimeField(default=timezone.now)
    cerrado_en = models.DateTimeField(null=True, blank=True)
    copia_trabajo_creada = models.BooleanField(default=False)
    copia_trabajo_creada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-iniciado_en"]
        verbose_name = "intento de simulación"
        verbose_name_plural = "intentos de simulación"
        constraints = [models.UniqueConstraint(fields=["estudiante", "caso_forense", "numero_intento"], name="intento_estudiante_caso_numero_uniq")]
        indexes = [
            models.Index(fields=["estudiante", "estado"], name="intento_estudiante_estado_idx"),
            models.Index(fields=["caso_forense", "iniciado_en"], name="intento_caso_fecha_idx"),
        ]

    def __str__(self):
        return f"Intento {self.numero_intento}: {self.estudiante} — {self.caso_forense}"

    @classmethod
    def siguiente_numero(cls, estudiante, caso_forense):
        ultimo = cls.objects.filter(estudiante=estudiante, caso_forense=caso_forense).aggregate(
            ultimo=models.Max("numero_intento")
        )["ultimo"] or 0
        return ultimo + 1


class RegistroActuacion(models.Model):
    class TipoAccion(models.TextChoices):
        DESCARGA_EVIDENCIA = "DESCARGA_EVIDENCIA", "Descarga de evidencia"
        CREACION_COPIA_TRABAJO = "CREACION_COPIA_TRABAJO", "Creación de copia de trabajo"
        VERIFICACION_HASH = "VERIFICACION_HASH", "Verificación de hash"
        INSPECCION_LOGS = "INSPECCION_LOGS", "Inspección de registros"
        IDENTIFICACION_INDICIO = "IDENTIFICACION_INDICIO", "Identificación de indicio"
        EXTRACCION_METADATOS = "EXTRACCION_METADATOS", "Extracción de metadatos"
        OTRA = "OTRA", "Otra acción"

    intento = models.ForeignKey(IntentoSimulacion, on_delete=models.CASCADE, related_name="actuaciones")
    tipo_accion = models.CharField(max_length=32, choices=TipoAccion.choices, db_index=True)
    detalle = models.TextField(blank=True)
    es_correcta = models.BooleanField(default=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["timestamp", "id"]
        verbose_name = "registro de actuación"
        verbose_name_plural = "registros de actuación"
        indexes = [models.Index(fields=["intento", "timestamp"], name="actuacion_intento_fecha_idx")]

    def __str__(self):
        return f"{self.get_tipo_accion_display()} — {self.timestamp:%Y-%m-%d %H:%M:%S}"


class CadenaCustodia(models.Model):
    intento = models.OneToOneField(IntentoSimulacion, on_delete=models.CASCADE, related_name="cadena_custodia")
    identificador_evidencia = models.CharField(max_length=120)
    descripcion = models.TextField()
    hash_registrado = models.CharField(max_length=64)
    fecha_hora_recoleccion = models.DateTimeField()
    origen = models.CharField(max_length=240)
    destino_transferencia = models.CharField(max_length=240)
    proposito_traslado = models.TextField()
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "cadena de custodia"
        verbose_name_plural = "cadenas de custodia"

    def __str__(self):
        return f"Cadena de custodia — {self.intento}"
