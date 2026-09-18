from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Announcement, Assignment, CalendarEvent, ClassRoom, Submission
from .permissions import (
    IsEventCreatorOrTeacher,
    IsMemberOfClassroom,
    IsOwnerOrTeacher,
    IsTeacherOfClassroom,
)
from .serializers import (
    AnnouncementSerializer,
    AssignmentSerializer,
    CalendarEventSerializer,
    ClassRoomDetailSerializer,
    ClassRoomSerializer,
    GradeSerializer,
    JoinClassSerializer,
    SubmissionSerializer,
)


class ClassRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacherOfClassroom]

    def get_queryset(self):
        user = self.request.user
        # El .distinct() es imprescindible: unir las dos consultas genera un
        # JOIN con la tabla de alumnos, así que sin él una clase aparecería
        # repetida una vez por cada alumno matriculado.
        #
        # select_related trae al profesor en la misma consulta, y annotate
        # calcula el número de alumnos en el propio SQL. Sin ellos, cada clase
        # de la lista disparaba dos consultas más (el clásico problema N+1).
        return (
            (ClassRoom.objects.filter(teacher=user) | ClassRoom.objects.filter(students=user))
            .distinct()
            .select_related("teacher")
            .prefetch_related("students")
            .annotate(num_students=Count("students", distinct=True))
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClassRoomDetailSerializer
        return ClassRoomSerializer

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def join(self, request):
        serializer = JoinClassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        classroom = get_object_or_404(ClassRoom, code=serializer.validated_data["code"])
        if classroom.teacher == request.user:
            return Response({"detail": "Eres el profesor de esta clase."}, status=status.HTTP_400_BAD_REQUEST)
        classroom.students.add(request.user)
        return Response(ClassRoomDetailSerializer(classroom).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def leave(self, request, pk=None):
        classroom = self.get_object()
        classroom.students.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberOfClassroom]

    def get_queryset(self):
        user = self.request.user
        classroom_id = self.request.query_params.get("classroom")
        qs = Announcement.objects.filter(classroom__in=ClassRoom.objects.filter(teacher=user)) | \
            Announcement.objects.filter(classroom__in=ClassRoom.objects.filter(students=user))
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs.distinct()

    def perform_create(self, serializer):
        classroom = serializer.validated_data["classroom"]
        if classroom.teacher != self.request.user:
            raise PermissionDenied("Solo el profesor puede publicar anuncios.")
        serializer.save(author=self.request.user)


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberOfClassroom]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        user = self.request.user
        classroom_id = self.request.query_params.get("classroom")
        qs = Assignment.objects.filter(classroom__in=ClassRoom.objects.filter(teacher=user)) | \
            Assignment.objects.filter(classroom__in=ClassRoom.objects.filter(students=user))
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs.distinct()

    def perform_create(self, serializer):
        classroom = serializer.validated_data["classroom"]
        if classroom.teacher != self.request.user:
            raise PermissionDenied("Solo el profesor puede crear tareas.")
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def submit(self, request, pk=None):
        assignment = self.get_object()
        if assignment.classroom.teacher == request.user:
            return Response({"detail": "El profesor no entrega tareas."}, status=status.HTTP_400_BAD_REQUEST)
        submission, _ = Submission.objects.update_or_create(
            assignment=assignment,
            student=request.user,
            defaults={
                "content": request.data.get("content", ""),
                "attachment": request.data.get("attachment"),
            },
        )
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_200_OK)


class CalendarEventViewSet(viewsets.ModelViewSet):
    """Exámenes, proyectos y otros eventos de las clases del usuario.

    Filtros opcionales por querystring:
      ?classroom=<id>   solo los eventos de esa clase
      ?month=YYYY-MM    solo los eventos de ese mes (lo usa la vista mensual)
    """

    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventCreatorOrTeacher]

    def get_queryset(self):
        user = self.request.user
        qs = CalendarEvent.objects.filter(classroom__in=ClassRoom.objects.filter(teacher=user)) | \
            CalendarEvent.objects.filter(classroom__in=ClassRoom.objects.filter(students=user))

        classroom_id = self.request.query_params.get("classroom")
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        month = self.request.query_params.get("month")
        if month:
            try:
                year, month_number = (int(part) for part in month.split("-"))
            except ValueError:
                raise ValidationError({"month": "Usa el formato YYYY-MM, por ejemplo 2026-09."})
            qs = qs.filter(date__year=year, date__month=month_number)

        return qs.distinct()

    def perform_create(self, serializer):
        classroom = serializer.validated_data["classroom"]
        is_member = (
            classroom.teacher == self.request.user
            or classroom.students.filter(pk=self.request.user.pk).exists()
        )
        if not is_member:
            raise PermissionDenied("Solo los miembros de la clase pueden añadir eventos.")
        serializer.save(created_by=self.request.user)


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacher]

    def get_queryset(self):
        user = self.request.user
        assignment_id = self.request.query_params.get("assignment")
        qs = Submission.objects.filter(student=user) | \
            Submission.objects.filter(assignment__classroom__teacher=user)
        if assignment_id:
            qs = qs.filter(assignment_id=assignment_id)
        return qs.distinct()

    def perform_create(self, serializer):
        classroom = serializer.validated_data["assignment"].classroom
        if classroom.teacher == self.request.user:
            raise PermissionDenied("El profesor no entrega tareas.")
        if not classroom.students.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("No estás matriculado en esta clase.")
        serializer.save(student=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def grade(self, request, pk=None):
        """Calificar una entrega. Reservado al profesor de la clase."""
        submission = self.get_object()
        if submission.assignment.classroom.teacher != request.user:
            raise PermissionDenied("Solo el profesor de la clase puede calificar.")

        serializer = GradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(submission, field, value)
        submission.save()
        return Response(SubmissionSerializer(submission).data)
