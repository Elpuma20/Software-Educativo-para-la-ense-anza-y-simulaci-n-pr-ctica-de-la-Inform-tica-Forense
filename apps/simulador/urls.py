from django.urls import path

from . import views

app_name = "simulador"

urlpatterns = [
    path("casos/", views.lista_casos, name="lista_casos"),
    path("casos/<int:caso_id>/intentos/iniciar/", views.iniciar_intento, name="iniciar_intento"),
    path("intentos/<int:intento_id>/", views.ver_intento, name="ver_intento"),
    path("intentos/<int:intento_id>/evidencia/", views.descargar_evidencia, name="descargar_evidencia"),
    path("api/intentos/<int:intento_id>/", views.obtener_caso_intento, name="obtener_caso_intento"),
    path("api/registrar-accion/", views.registrar_accion, name="registrar_accion"),
]
