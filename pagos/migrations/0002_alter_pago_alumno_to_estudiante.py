from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estudiantes', '0001_initial'),
        ('pagos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pago',
            name='alumno',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='pagos',
                to='estudiantes.estudiante',
            ),
        ),
    ]
