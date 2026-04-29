from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estudiantes', '0001_initial'),
        ('matriculas', '0003_alter_matricula_aula_not_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matricula',
            name='alumno',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='matriculas',
                to='estudiantes.estudiante',
            ),
        ),
    ]
