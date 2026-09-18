from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Announcement, Assignment, CalendarEvent, ClassRoom, Submission


class ClassRoomSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    def get_student_count(self, obj):
        # La lista de clases llega ya anotada desde la consulta, así que no
        # hace falta contar de nuevo. Si el objeto viene suelto (por ejemplo
        # al unirse a una clase), contamos sobre la marcha.
        annotated = getattr(obj, "num_students", None)
        return annotated if annotated is not None else obj.students.count()

    class Meta:
        model = ClassRoom
        fields = [
            "id", "name", "section", "subject", "description",
            "code", "teacher", "student_count", "created_at",
        ]
        read_only_fields = ["id", "code", "teacher", "created_at"]


class ClassRoomDetailSerializer(ClassRoomSerializer):
    students = UserSerializer(many=True, read_only=True)

    class Meta(ClassRoomSerializer.Meta):
        fields = ClassRoomSerializer.Meta.fields + ["students"]


class JoinClassSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate_code(self, value):
        value = value.strip().upper()
        if not ClassRoom.objects.filter(code=value).exists():
            raise serializers.ValidationError("No existe ninguna clase con ese código.")
        return value


class AnnouncementSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Announcement
        fields = ["id", "classroom", "author", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    my_submission = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id", "classroom", "title", "description",
            "due_date", "points", "created_at", "my_submission",
        ]
        read_only_fields = ["id", "created_at"]

    def get_my_submission(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        submission = obj.submissions.filter(student=request.user).first()
        return SubmissionSerializer(submission).data if submission else None


class CalendarEventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)

    class Meta:
        model = CalendarEvent
        fields = [
            "id", "classroom", "classroom_name", "created_by",
            "title", "description", "event_type", "date", "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]


class SubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "assignment", "student", "content", "attachment",
            "submitted_at", "grade", "feedback",
        ]
        # grade y feedback son de solo lectura aquí a propósito: si fueran
        # escribibles, un estudiante podría ponerse su propia nota al crear
        # la entrega. Se escriben solo desde /api/submissions/<id>/grade/.
        read_only_fields = ["id", "student", "submitted_at", "grade", "feedback"]


class GradeSerializer(serializers.Serializer):
    """Datos que el profesor manda al calificar una entrega."""

    grade = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    feedback = serializers.CharField(required=False, allow_blank=True)
