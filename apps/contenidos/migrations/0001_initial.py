from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="TemaTeorico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("orden", models.PositiveIntegerField(db_index=True, default=0)),
                ("contenido_markdown", models.TextField(verbose_name="contenido en Markdown")),
                ("objetivos_aprendizaje", models.TextField(blank=True)),
                ("publicado", models.BooleanField(db_index=True, default=False)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="temas_creados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "tema teórico", "verbose_name_plural": "temas teóricos", "ordering": ["orden", "titulo"]},
        ),
        migrations.AddIndex(model_name="temateorico", index=models.Index(fields=["publicado", "orden"], name="tema_publicado_orden_idx")),
    ]
