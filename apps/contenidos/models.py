from django.conf import settings
from django.db import models


class TemaTeorico(models.Model):
    titulo = models.CharField(max_length=180)
    orden = models.PositiveIntegerField(default=0, db_index=True)
    contenido_markdown = models.TextField(verbose_name="contenido en Markdown")
    objetivos_aprendizaje = models.TextField(blank=True)
    publicado = models.BooleanField(default=False, db_index=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="temas_creados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["orden", "titulo"]
        verbose_name = "tema teórico"
        verbose_name_plural = "temas teóricos"
        indexes = [models.Index(fields=["publicado", "orden"], name="tema_publicado_orden_idx")]

    def __str__(self):
        return self.titulo
