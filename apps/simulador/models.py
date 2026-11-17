import hashlib

from django.core.validators import RegexValidator
from django.db import models

validar_sha256 = RegexValidator(r"\A[a-fA-F0-9]{64}\Z", "El hash debe contener exactamente 64 caracteres hexadecimales.")


class CasoForense(models.Model):
    class Dificultad(models.TextChoices):
        BASICA = "BASICA", "Básica"
        INTERMEDIA = "INTERMEDIA", "Intermedia"
        AVANZADA = "AVANZADA", "Avanzada"

    titulo = models.CharField(max_length=180)
    descripcion_escenario = models.TextField()
    dificultad = models.CharField(max_length=12, choices=Dificultad.choices, default=Dificultad.BASICA, db_index=True)
    tema_teorico = models.ForeignKey(
        "contenidos.TemaTeorico", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="casos_practicos",
    )
    archivo_evidencia = models.FileField(upload_to="evidencias/casos/", blank=True)
    hash_sha256_original = models.CharField(max_length=64, blank=True, validators=[validar_sha256])
    hash_sha256_alterado = models.CharField(max_length=64, blank=True, validators=[validar_sha256])
    registro_actividad = models.JSONField(default=dict, blank=True, help_text="Registros sintéticos preparados para el caso.")
    hallazgos_esperados = models.JSONField(default=list, blank=True)
    activo = models.BooleanField(default=True, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titulo"]
        verbose_name = "caso forense"
        verbose_name_plural = "casos forenses"
        indexes = [models.Index(fields=["activo", "dificultad"], name="caso_activo_dificultad_idx")]

    def __str__(self):
        return self.titulo

    def calcular_hash_evidencia(self):
        """Calcula SHA-256 leyendo en fragmentos el archivo de evidencia asociado."""
        if not self.archivo_evidencia:
            raise ValueError("El caso no tiene un archivo de evidencia asociado.")
        resumen = hashlib.sha256()
        self.archivo_evidencia.open("rb")
        try:
            for fragmento in self.archivo_evidencia.chunks():
                resumen.update(fragmento)
        finally:
            self.archivo_evidencia.close()
        return resumen.hexdigest()
