from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "docente_aprobado", "is_active", "is_staff")
    list_filter = ("rol", "docente_aprobado", "is_active", "is_staff")
    search_fields = ("username", "email", "cedula", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (("Datos académicos", {"fields": ("rol", "cedula", "docente_aprobado")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Datos académicos", {"fields": ("rol", "cedula", "docente_aprobado")}),)
