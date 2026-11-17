import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("simulador", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="IntentoSimulacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_intento", models.PositiveIntegerField()),
                ("estado", models.CharField(choices=[("EN_PROGRESO", "En progreso"), ("COMPLETADO", "Completado")], db_index=True, default="EN_PROGRESO", max_length=12)),
                ("puntaje_automatico", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("puntaje_docente", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("retroalimentacion", models.TextField(blank=True)),
                ("iniciado_en", models.DateTimeField(default=django.utils.timezone.now)),
                ("cerrado_en", models.DateTimeField(blank=True, null=True)),
                ("copia_trabajo_creada", models.BooleanField(default=False)),
                ("copia_trabajo_creada_en", models.DateTimeField(blank=True, null=True)),
                ("caso_forense", models.ForeignKey(on_delete=models.PROTECT, related_name="intentos", to="simulador.casoforense")),
                ("estudiante", models.ForeignKey(on_delete=models.PROTECT, related_name="intentos_simulacion", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "intento de simulación", "verbose_name_plural": "intentos de simulación", "ordering": ["-iniciado_en"]},
        ),
        migrations.CreateModel(
            name="CadenaCustodia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("identificador_evidencia", models.CharField(max_length=120)),
                ("descripcion", models.TextField()),
                ("hash_registrado", models.CharField(max_length=64)),
                ("fecha_hora_recoleccion", models.DateTimeField()),
                ("origen", models.CharField(max_length=240)),
                ("destino_transferencia", models.CharField(max_length=240)),
                ("proposito_traslado", models.TextField()),
                ("observaciones", models.TextField(blank=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("intento", models.OneToOneField(on_delete=models.CASCADE, related_name="cadena_custodia", to="evaluacion.intentosimulacion")),
            ],
            options={"verbose_name": "cadena de custodia", "verbose_name_plural": "cadenas de custodia"},
        ),
        migrations.CreateModel(
            name="RegistroActuacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo_accion", models.CharField(choices=[("DESCARGA_EVIDENCIA", "Descarga de evidencia"), ("CREACION_COPIA_TRABAJO", "Creación de copia de trabajo"), ("VERIFICACION_HASH", "Verificación de hash"), ("INSPECCION_LOGS", "Inspección de registros"), ("IDENTIFICACION_INDICIO", "Identificación de indicio"), ("EXTRACCION_METADATOS", "Extracción de metadatos"), ("OTRA", "Otra acción")], db_index=True, max_length=32)),
                ("detalle", models.TextField(blank=True)),
                ("es_correcta", models.BooleanField(db_index=True, default=True)),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("intento", models.ForeignKey(on_delete=models.CASCADE, related_name="actuaciones", to="evaluacion.intentosimulacion")),
            ],
            options={"verbose_name": "registro de actuación", "verbose_name_plural": "registros de actuación", "ordering": ["timestamp", "id"]},
        ),
        migrations.AddConstraint(
            model_name="intentosimulacion",
            constraint=models.UniqueConstraint(fields=("estudiante", "caso_forense", "numero_intento"), name="intento_estudiante_caso_numero_uniq"),
        ),
        migrations.AddIndex(model_name="intentosimulacion", index=models.Index(fields=["estudiante", "estado"], name="intento_estudiante_estado_idx")),
        migrations.AddIndex(model_name="intentosimulacion", index=models.Index(fields=["caso_forense", "iniciado_en"], name="intento_caso_fecha_idx")),
        migrations.AddIndex(model_name="registroactuacion", index=models.Index(fields=["intento", "timestamp"], name="actuacion_intento_fecha_idx")),
    ]
