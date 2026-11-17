from django.urls import path

from . import views

app_name = "contenidos"

urlpatterns = [
    path("", views.lista_temas, name="lista_temas"),
    path("<int:tema_id>/", views.detalle_tema, name="detalle_tema"),
]
