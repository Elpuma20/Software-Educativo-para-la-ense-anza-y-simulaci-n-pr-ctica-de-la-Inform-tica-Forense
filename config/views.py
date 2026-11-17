from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def inicio(request):
    if request.user.is_superuser or getattr(request.user, "es_docente_aprobado", False):
        return redirect("admin:index")
    return redirect("simulador:lista_casos")
