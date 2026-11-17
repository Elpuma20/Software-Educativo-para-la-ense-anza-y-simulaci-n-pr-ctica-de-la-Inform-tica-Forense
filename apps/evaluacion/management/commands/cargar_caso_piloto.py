import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.contenidos.models import TemaTeorico
from apps.simulador.models import CasoForense

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Crea usuarios de demostración y un caso forense sintético de ejemplo."

    @transaction.atomic
    def handle(self, *args, **opciones):
        docente, clave_docente, docente_creado = self._obtener_usuario(
            username="docente_demo", rol=Usuario.Rol.DOCENTE, cedula="DEMO-DOCENTE-001",
            docente_aprobado=True,
        )
        estudiante, clave_estudiante, estudiante_creado = self._obtener_usuario(
            username="estudiante_demo", rol=Usuario.Rol.ESTUDIANTE, cedula="DEMO-ESTUDIANTE-001",
        )

        tema, _ = TemaTeorico.objects.update_or_create(
            titulo="Preservación de evidencia digital",
            defaults={
                "orden": 1,
                "contenido_markdown": (
                    "## Principio de preservación\n\n"
                    "La evidencia digital debe preservarse sin alterar el original. "
                    "Documenta su recepción, genera una copia de trabajo y realiza "
                    "los análisis sobre esa copia. Registra el hash SHA-256 y cada transferencia."
                ),
                "objetivos_aprendizaje": "Preservar evidencia, crear una copia de trabajo y documentar la cadena de custodia.",
                "publicado": True,
                "creado_por": docente,
            },
        )
        caso, _ = CasoForense.objects.update_or_create(
            titulo="Imagen de disco de laboratorio",
            defaults={
                "descripcion_escenario": (
                    "Se recibe un archivo de texto sintético que representa una imagen de disco. "
                    "Documenta su recepción, crea una copia de trabajo e inspecciona los registros simulados."
                ),
                "dificultad": CasoForense.Dificultad.BASICA,
                "tema_teorico": tema,
                "registro_actividad": {
                    "formato": "JSON sintético",
                    "eventos": [
                        {"hora": "2026-01-14T09:12:00Z", "evento": "sesion_iniciada", "usuario": "alumno_lab"},
                        {"hora": "2026-01-14T09:16:32Z", "evento": "archivo_creado", "ruta": "/home/alumno/notas.txt"},
                        {"hora": "2026-01-14T09:18:07Z", "evento": "archivo_copiado", "ruta": "/media/externo/datos.zip"},
                    ],
                },
                "hallazgos_esperados": [
                    "El original debe preservarse sin análisis directo.",
                    "La copia de trabajo debe generarse antes de la inspección.",
                    "Los registros muestran la creación de notas y la copia de un archivo comprimido.",
                ],
                "activo": True,
            },
        )

        contenido_evidencia = (
            "EVIDENCIA SINTÉTICA PARA FINES EDUCATIVOS\n"
            "Identificador: LAB-IMG-001\n"
            "Este archivo no contiene datos reales ni evidencia de una investigación.\n"
            "Usar únicamente para prácticas académicas en el simulador.\n"
        ).encode("utf-8")
        if not caso.archivo_evidencia:
            caso.archivo_evidencia.save("evidencia_sintetica_lab.txt", ContentFile(contenido_evidencia), save=False)
        caso.hash_sha256_original = hashlib.sha256(contenido_evidencia).hexdigest()
        caso.hash_sha256_alterado = hashlib.sha256(contenido_evidencia + b"\nALTERACION DE LABORATORIO\n").hexdigest()
        caso.save()

        self.stdout.write(self.style.SUCCESS("El caso piloto está listo."))
        self.stdout.write(f"Docente: {docente.username} (aprobado: {docente.docente_aprobado})")
        self.stdout.write(f"Estudiante: {estudiante.username}")
        self.stdout.write(f"Tema: {tema.titulo}")
        self.stdout.write(f"Caso: {caso.titulo} (ID {caso.pk})")
        self.stdout.write(f"SHA-256 sintético: {caso.hash_sha256_original}")
        if docente_creado:
            self.stdout.write(self.style.WARNING(f"Contraseña inicial del docente (guárdala): {clave_docente}"))
        else:
            self.stdout.write("El docente ya existía; se conservó su contraseña.")
        if estudiante_creado:
            self.stdout.write(self.style.WARNING(f"Contraseña inicial del estudiante (guárdala): {clave_estudiante}"))
        else:
            self.stdout.write("El estudiante ya existía; se conservó su contraseña.")
        self.stdout.write("Para iniciar un intento, envía POST a /simulador/casos/{}/intentos/iniciar/.".format(caso.pk))

    def _obtener_usuario(self, username, rol, cedula, docente_aprobado=False):
        usuario, creado = Usuario.objects.get_or_create(
            username=username,
            defaults={"rol": rol, "cedula": cedula, "docente_aprobado": docente_aprobado, "is_active": True},
        )
        if creado:
            clave = secrets.token_urlsafe(18)
            usuario.set_password(clave)
            usuario.save(update_fields=["password"])
        else:
            clave = None
            # La cuenta de demostración docente queda aprobada por el comando piloto.
            cambios = []
            if rol == Usuario.Rol.DOCENTE and not usuario.docente_aprobado:
                usuario.docente_aprobado = True
                cambios.append("docente_aprobado")
            if not usuario.is_active:
                usuario.is_active = True
                cambios.append("is_active")
            if cambios:
                usuario.save(update_fields=cambios)
        return usuario, clave, creado
