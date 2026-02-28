# Generated migration for SOA auto-generation support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="soaversion",
            name="source",
            field=models.CharField(
                choices=[("UPLOAD", "Upload"), ("GENERATED", "Generated")],
                default="UPLOAD",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="soaversion",
            name="uploaded_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="uploaded_soas",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
