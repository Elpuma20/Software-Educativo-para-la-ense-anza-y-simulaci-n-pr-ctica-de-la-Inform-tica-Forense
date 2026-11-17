from django.contrib import admin
from django.urls import include, path
from apps.simulador.views import registrar_accion
from .views import inicio

urlpatterns = [
    path("", inicio, name="inicio"),
    path("admin/", admin.site.urls),
    path("cuentas/", include("django.contrib.auth.urls")),
    path("contenidos/", include("apps.contenidos.urls")),
    path("simulador/", include("apps.simulador.urls")),
    path("api/simulador/registrar-accion/", registrar_accion, name="registrar_accion_api"),
    path("api/evaluacion/", include("apps.evaluacion.urls")),
]
