import django.core.validators
from django.db import migrations, models


validar_sha256 = django.core.validators.RegexValidator(r"\A[a-fA-F0-9]{64}\Z", "El hash debe contener exactamente 64 caracteres hexadecimales.")


class Migration(migrations.Migration):
    initial = True
    dependencies = [("contenidos", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="CasoForense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("descripcion_escenario", models.TextField()),
                ("dificultad", models.CharField(choices=[("BASICA", "Básica"), ("INTERMEDIA", "Intermedia"), ("AVANZADA", "Avanzada")], db_index=True, default="BASICA", max_length=12)),
                ("archivo_evidencia", models.FileField(blank=True, upload_to="evidencias/casos/")),
                ("hash_sha256_original", models.CharField(blank=True, max_length=64, validators=[validar_sha256])),
                ("hash_sha256_alterado", models.CharField(blank=True, max_length=64, validators=[validar_sha256])),
                ("registro_actividad", models.JSONField(blank=True, default=dict, help_text="Registros sintéticos preparados para el caso.")),
                ("hallazgos_esperados", models.JSONField(blank=True, default=list)),
                ("activo", models.BooleanField(db_index=True, default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("tema_teorico", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="casos_practicos", to="contenidos.temateorico")),
            ],
            options={"verbose_name": "caso forense", "verbose_name_plural": "casos forenses", "ordering": ["titulo"]},
        ),
        migrations.AddIndex(model_name="casoforense", index=models.Index(fields=["activo", "dificultad"], name="caso_activo_dificultad_idx")),
    ]
