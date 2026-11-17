from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class GestorUsuario(BaseUserManager):
    """Crea usuarios y superusuarios usando el modelo personalizado."""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")
        correo = extra_fields.get("email")
        if correo:
            extra_fields["email"] = self.normalize_email(correo)
        usuario = self.model(username=username, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("rol", Usuario.Rol.DOCENTE)
        extra_fields.setdefault("docente_aprobado", True)
        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError("El superusuario debe tener permisos de staff y superusuario.")
        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ESTUDIANTE = "ESTUDIANTE", "Estudiante"
        DOCENTE = "DOCENTE", "Docente"

    rol = models.CharField(max_length=12, choices=Rol.choices, default=Rol.ESTUDIANTE, db_index=True)
    cedula = models.CharField(max_length=24, unique=True, null=True, blank=True, verbose_name="cédula")
    docente_aprobado = models.BooleanField(default=False, help_text="El administrador aprueba el acceso docente.")

    objects = GestorUsuario()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        indexes = [models.Index(fields=["rol", "is_active"], name="usuario_rol_activo_idx")]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE

    @property
    def es_docente_aprobado(self):
        return self.rol == self.Rol.DOCENTE and self.docente_aprobado
