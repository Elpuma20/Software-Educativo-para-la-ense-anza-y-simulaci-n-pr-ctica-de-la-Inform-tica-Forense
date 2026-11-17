from django.contrib import admin

from .models import CasoForense


@admin.register(CasoForense)
class CasoForenseAdmin(admin.ModelAdmin):
    list_display = ("titulo", "dificultad", "tema_teorico", "activo")
    list_filter = ("dificultad", "activo")
    search_fields = ("titulo", "descripcion_escenario")
