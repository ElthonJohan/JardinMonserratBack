from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matriculas', '0002_matricula_aula_remove_grado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matricula',
            name='aula',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='matriculas',
                to='estudiantes.aula',
            ),
        ),
    ]
