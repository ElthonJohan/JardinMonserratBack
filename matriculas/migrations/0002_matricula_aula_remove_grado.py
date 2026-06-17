from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estudiantes', '0001_initial'),
        ('core', '0001_initial'),
        ('matriculas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='matricula',
            name='aula',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='matriculas', to='estudiantes.aula'),
        ),
        migrations.RemoveField(
            model_name='matricula',
            name='grado',
        ),
    ]
