from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Usuario

NOMBRE_GRUPO_DOCENTES = "Docentes aprobados"
PERMISOS_DOCENTE = {
    ("contenidos", "temateorico", "add"),
    ("contenidos", "temateorico", "change"),
    ("contenidos", "temateorico", "view"),
    ("simulador", "casoforense", "add"),
    ("simulador", "casoforense", "change"),
    ("simulador", "casoforense", "view"),
    ("evaluacion", "intentosimulacion", "view"),
    ("evaluacion", "registroactuacion", "view"),
    ("evaluacion", "cadenacustodia", "view"),
}


@receiver(post_migrate, dispatch_uid="usuarios.configurar_grupo_docentes")
def configurar_grupo_docentes(sender, **kwargs):
    """Crea el grupo docente con permisos mínimos tras crear las tablas y permisos."""
    grupo, _ = Group.objects.get_or_create(name=NOMBRE_GRUPO_DOCENTES)
    permisos = Permission.objects.none()
    for app_label, modelo, accion in PERMISOS_DOCENTE:
        permisos = permisos | Permission.objects.filter(
            content_type__app_label=app_label,
            content_type__model=modelo,
            codename=f"{accion}_{modelo}",
        )
    grupo.permissions.set(permisos.distinct())
    for usuario in Usuario.objects.filter(rol=Usuario.Rol.DOCENTE, docente_aprobado=True):
        _sincronizar_usuario_docente(usuario)


@receiver(post_save, sender=Usuario, dispatch_uid="usuarios.sincronizar_permisos_docente")
def sincronizar_permisos_docente(sender, instance, **kwargs):
    _sincronizar_usuario_docente(instance)


def _sincronizar_usuario_docente(usuario):
    grupo = Group.objects.filter(name=NOMBRE_GRUPO_DOCENTES).first()
    if grupo is None:
        return
    aprobado = usuario.rol == Usuario.Rol.DOCENTE and usuario.docente_aprobado
    if aprobado:
        grupo.user_set.add(usuario)
        if not usuario.is_staff and not usuario.is_superuser:
            Usuario.objects.filter(pk=usuario.pk).update(is_staff=True)
    else:
        grupo.user_set.remove(usuario)
        if usuario.rol == Usuario.Rol.DOCENTE and usuario.is_staff and not usuario.is_superuser:
            Usuario.objects.filter(pk=usuario.pk).update(is_staff=False)
