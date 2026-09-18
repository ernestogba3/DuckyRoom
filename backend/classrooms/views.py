from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Announcement, Assignment, ClassRoom, Submission
from .permissions import IsMemberOfClassroom, IsOwnerOrTeacher, IsTeacherOfClassroom
from .serializers import (
    AnnouncementSerializer,
    AssignmentSerializer,
    ClassRoomDetailSerializer,
    ClassRoomSerializer,
    JoinClassSerializer,
    SubmissionSerializer,
)


class ClassRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacherOfClassroom]

    def get_queryset(self):
        user = self.request.user
        return ClassRoom.objects.filter(teacher=user) | ClassRoom.objects.filter(students=user)

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
            raise permissions.PermissionDenied("Solo el profesor puede publicar anuncios.")
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
            raise permissions.PermissionDenied("Solo el profesor puede crear tareas.")
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
        serializer.save(student=self.request.user)
