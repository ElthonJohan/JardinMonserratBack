from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('matriculas', '0004_alter_matricula_alumno_to_estudiante'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='matricula',
            name='seccion',
        ),
    ]
