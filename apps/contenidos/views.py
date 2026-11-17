from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.usuarios.permissions import estudiante_required
from .models import TemaTeorico


@require_GET
@estudiante_required
def lista_temas(request):
    temas = TemaTeorico.objects.filter(publicado=True).order_by("orden", "titulo")
    return render(request, "contenidos/lista_temas.html", {"temas": temas})


@require_GET
@estudiante_required
def detalle_tema(request, tema_id):
    tema = get_object_or_404(TemaTeorico, pk=tema_id, publicado=True)
    return render(request, "contenidos/detalle_tema.html", {"tema": tema})
