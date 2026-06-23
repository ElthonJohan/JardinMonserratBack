from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F

from .models import PeriodoEvaluacion, Area, Competencia, Calificacion, Apreciacion, AsignacionDocente
from .serializers import (
    PeriodoEvaluacionSerializer, AreaSerializer, CompetenciaSerializer,
    CalificacionSerializer, ApreciacionSerializer, AsignacionDocenteSerializer
)
from estudiantes.models import Estudiante
from matriculas.models import Matricula

class LecturaPadresEscrituraDocentes(BasePermission):
    """
    Permite acceso de solo lectura a padres (usuarios autenticados),
    y escritura a docentes o administradores.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        # Asumiendo que is_staff abarca a administradores y docentes configurados
        return request.user.is_staff or request.user.is_superuser

class SoloAdminManejoAsignacion(BasePermission):
    """
    Permite lectura a cualquier usuario autenticado,
    pero restringe la escritura/edición únicamente a administradores (is_staff o is_superuser).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.is_superuser

class PeriodoEvaluacionViewSet(viewsets.ModelViewSet):
    queryset = PeriodoEvaluacion.objects.all()
    serializer_class = PeriodoEvaluacionSerializer
    permission_classes = [IsAuthenticated, LecturaPadresEscrituraDocentes]
    filterset_fields = ['activo', 'periodo_matricula']

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated, LecturaPadresEscrituraDocentes]
    filterset_fields = ['activo']
    ordering_fields = ['orden']
    ordering = ['orden']

class CompetenciaViewSet(viewsets.ModelViewSet):
    queryset = Competencia.objects.all()
    serializer_class = CompetenciaSerializer
    permission_classes = [IsAuthenticated, LecturaPadresEscrituraDocentes]
    filterset_fields = ['area', 'activo']
    ordering_fields = ['area', 'orden']
    ordering = ['area', 'orden']

class CalificacionViewSet(viewsets.ModelViewSet):
    queryset = Calificacion.objects.all()
    serializer_class = CalificacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_fields = ['alumno', 'periodo_evaluacion', 'competencia']

    def perform_create(self, serializer):
        serializer.save(docente_evaluador=self.request.user)

    def perform_update(self, serializer):
        serializer.save(docente_evaluador=self.request.user)

    @action(detail=False, methods=['post'])
    def bulk_guardar(self, request):
        """
        Guarda o actualiza calificaciones masivamente.
        Recibe una lista: [{"alumno_id": 1, "competencia_id": 2, "periodo_evaluacion_id": 1, "valor": "A"}, ...]
        """
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Se espera una lista de objetos"}, status=status.HTTP_400_BAD_REQUEST)
        
        valid_items = []
        for item in data:
            alumno_id = item.get('alumno_id')
            competencia_id = item.get('competencia_id')
            periodo_evaluacion_id = item.get('periodo_evaluacion_id')
            valor = item.get('valor')

            if not all([alumno_id, competencia_id, periodo_evaluacion_id, valor]):
                continue
            
            # Obtener matrícula activa
            matricula = Matricula.objects.filter(alumno_id=alumno_id, estado='Activa').first()
            if not matricula:
                return Response(
                    {"error": f"El alumno con ID {alumno_id} no posee una matrícula activa."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Si no es administrador o staff, validar asignación docente
            if not (request.user.is_staff or request.user.is_superuser):
                try:
                    competencia = Competencia.objects.select_related('area').get(id=competencia_id)
                except Competencia.DoesNotExist:
                    return Response(
                        {"error": f"La competencia con ID {competencia_id} no existe."},
                        status=status.HTTP_403_FORBIDDEN
                    )

                tiene_asignacion = AsignacionDocente.objects.filter(
                    docente=request.user,
                    aula=matricula.aula,
                    areas=competencia.area,
                    periodo_matricula=matricula.periodo_academico,
                    activo=True
                ).exists()

                if not tiene_asignacion:
                    return Response(
                        {"error": f"No autorizado: No tiene una asignación activa para el área '{competencia.area.nombre}' en el aula del estudiante."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            valid_items.append((alumno_id, competencia_id, periodo_evaluacion_id, valor))

        resultados = []
        try:
            with transaction.atomic():
                for alumno_id, competencia_id, periodo_evaluacion_id, valor in valid_items:
                    calificacion, created = Calificacion.objects.update_or_create(
                        alumno_id=alumno_id,
                        competencia_id=competencia_id,
                        periodo_evaluacion_id=periodo_evaluacion_id,
                        defaults={
                            'valor': valor,
                            'docente_evaluador': request.user
                        }
                    )
                    resultados.append(calificacion.id)
            return Response({"mensaje": f"Se guardaron/actualizaron {len(resultados)} calificaciones exitosamente."})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ApreciacionViewSet(viewsets.ModelViewSet):
    queryset = Apreciacion.objects.all()
    serializer_class = ApreciacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_fields = ['alumno', 'periodo_evaluacion']

    def get_queryset(self):
        queryset = Apreciacion.objects.all()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        if not (user.is_staff or user.is_superuser):
            student_ids = Matricula.objects.filter(
                estado='Activa',
                aula__asignaciones_docentes__docente=user,
                aula__asignaciones_docentes__activo=True,
                aula__asignaciones_docentes__periodo_matricula=F('periodo_academico')
            ).values_list('alumno_id', flat=True)
            queryset = queryset.filter(alumno_id__in=student_ids)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            alumno = serializer.validated_data.get('alumno')
            matricula = Matricula.objects.filter(alumno_id=alumno.id, estado='Activa').first()
            if not matricula:
                raise PermissionDenied("El estudiante no cuenta con una matrícula activa.")
            
            tiene_asignacion = AsignacionDocente.objects.filter(
                docente=user,
                aula=matricula.aula,
                periodo_matricula=matricula.periodo_academico,
                activo=True
            ).exists()
            if not tiene_asignacion:
                raise PermissionDenied("No autorizado: No tiene una asignación docente activa en el aula de este alumno.")

        serializer.save(docente=user)

    def perform_update(self, serializer):
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            instance = self.get_object()
            alumno = serializer.validated_data.get('alumno', instance.alumno)
            matricula = Matricula.objects.filter(alumno_id=alumno.id, estado='Activa').first()
            if not matricula:
                raise PermissionDenied("El estudiante no cuenta con una matrícula activa.")
            
            tiene_asignacion = AsignacionDocente.objects.filter(
                docente=user,
                aula=matricula.aula,
                periodo_matricula=matricula.periodo_academico,
                activo=True
            ).exists()
            if not tiene_asignacion:
                raise PermissionDenied("No autorizado: No tiene una asignación docente activa en el aula de este alumno.")

        serializer.save(docente=user)

class AsignacionDocenteViewSet(viewsets.ModelViewSet):
    queryset = AsignacionDocente.objects.all()
    serializer_class = AsignacionDocenteSerializer
    permission_classes = [IsAuthenticated, SoloAdminManejoAsignacion]
    filterset_fields = ['docente', 'aula', 'areas', 'periodo_matricula', 'activo']

    @action(detail=False, methods=['get'], url_path='mis-cursos')
    def mis_cursos(self, request):
        asignaciones = self.get_queryset().filter(docente=request.user, activo=True)
        serializer = self.get_serializer(asignaciones, many=True)
        data = serializer.data

        for i, asignacion in enumerate(asignaciones):
            matriculas_activas = Matricula.objects.filter(
                aula=asignacion.aula,
                periodo_academico=asignacion.periodo_matricula,
                estado='Activa'
            ).select_related('alumno')

            alumnos_list = []
            for mat in matriculas_activas:
                alumnos_list.append({
                    "id": mat.alumno.id,
                    "nombres": mat.alumno.nombres,
                    "apellidos": mat.alumno.apellidos,
                    "codigo_estudiante": mat.alumno.codigo_estudiante,
                    "dni": mat.alumno.dni,
                })
            data[i]['alumnos'] = alumnos_list

        return Response(data)

class LibretaVirtualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alumno_id = request.query_params.get('alumno_id')
        periodo_id = request.query_params.get('periodo_evaluacion_id')

        if not alumno_id or not periodo_id:
            return Response(
                {"error": "Faltan parámetros alumno_id o periodo_evaluacion_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alumno = get_object_or_404(Estudiante, id=alumno_id)
        periodo = get_object_or_404(PeriodoEvaluacion, id=periodo_id)

        calificaciones = Calificacion.objects.filter(
            alumno=alumno, 
            periodo_evaluacion=periodo
        ).select_related('competencia', 'competencia__area').order_by('competencia__area__orden', 'competencia__orden')
        
        apreciacion_obj = Apreciacion.objects.filter(alumno=alumno, periodo_evaluacion=periodo).first()

        areas_dict = {}
        for cal in calificaciones:
            area_nombre = cal.competencia.area.nombre
            if area_nombre not in areas_dict:
                areas_dict[area_nombre] = []
            
            areas_dict[area_nombre].append({
                "descripcion": cal.competencia.descripcion,
                "nota": cal.valor
            })
        
        areas_list = [{"area": k, "competencias": v} for k, v in areas_dict.items()]

        return Response({
            "alumno": f"{alumno.nombres} {alumno.apellidos}",
            "periodo": periodo.nombre,
            "areas": areas_list,
            "apreciacion": apreciacion_obj.comentario if apreciacion_obj else ""
        })
