from django.urls import path

from . import views

app_name = "evaluacion"

urlpatterns = [
    path("intentos/<int:intento_id>/resultado/", views.ver_resultado, name="ver_resultado"),
    path("intentos/<int:intento_id>/finalizar/", views.finalizar_intento, name="finalizar_intento"),
    path("intentos/<int:intento_id>/", views.revisar_intento, name="revisar_intento"),
    path("intentos/<int:intento_id>/calificar/", views.calificar_intento, name="calificar_intento"),
]
