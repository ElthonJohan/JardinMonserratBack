from rest_framework import serializers
from .models import Notificacion

class NotificacionSerializer(serializers.ModelSerializer):
    alumno_id = serializers.IntegerField(source='alumno.id', read_only=True)
    alumno_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = ['id', 'usuario', 'alumno_id', 'alumno_nombre', 'titulo', 'mensaje', 'tipo', 'leido', 'fecha_creacion']
        read_only_fields = ['id', 'usuario', 'titulo', 'mensaje', 'tipo', 'fecha_creacion']

    def get_alumno_nombre(self, obj):
        if obj.alumno:
            return f"{obj.alumno.nombres} {obj.alumno.apellidos}"
        return None
