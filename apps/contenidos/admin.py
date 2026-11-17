from django.contrib import admin

from .models import TemaTeorico


@admin.register(TemaTeorico)
class TemaTeoricoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "orden", "publicado", "actualizado_en")
    list_filter = ("publicado",)
    search_fields = ("titulo", "contenido_markdown")
    ordering = ("orden", "titulo")
