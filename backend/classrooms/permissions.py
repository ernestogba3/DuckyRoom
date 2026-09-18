from rest_framework import permissions


def es_miembro(classroom, user):
    """¿El usuario es el profesor o un alumno matriculado?

    Usa .exists() en lugar de `user in classroom.students.all()`, que traería
    a todos los alumnos de la clase a memoria solo para comprobar a uno.
    """
    if classroom.teacher_id == user.id:
        return True
    return classroom.students.filter(pk=user.pk).exists()


class IsTeacherOfClassroom(permissions.BasePermission):
    """Solo el profesor dueño de la clase puede modificarla."""

    def has_object_permission(self, request, view, obj):
        classroom = obj if hasattr(obj, "teacher") else obj.classroom
        if request.method in permissions.SAFE_METHODS:
            return es_miembro(classroom, request.user)
        return classroom.teacher == request.user


class IsMemberOfClassroom(permissions.BasePermission):
    """El usuario debe ser el profesor o un estudiante inscrito en la clase."""

    def has_object_permission(self, request, view, obj):
        classroom = obj if hasattr(obj, "teacher") else obj.classroom
        return es_miembro(classroom, request.user)


class IsEventCreatorOrTeacher(permissions.BasePermission):
    """Cualquier miembro lee los eventos; solo quien lo creó (o el profesor) lo edita o borra."""

    def has_object_permission(self, request, view, obj):
        classroom = obj.classroom
        if request.method in permissions.SAFE_METHODS:
            return es_miembro(classroom, request.user)
        return obj.created_by == request.user or classroom.teacher == request.user


class IsOwnerOrTeacher(permissions.BasePermission):
    """Para entregas: el estudiante dueño edita su entrega; el profesor califica.

    Nos fijamos en QUÉ acción se está ejecutando, no en los campos que vengan
    en el cuerpo de la petición: mirar el cuerpo es frágil, porque basta con
    cambiar el nombre de un campo para saltarse la comprobación.
    """

    def has_object_permission(self, request, view, obj):
        is_owner = obj.student == request.user
        is_teacher = obj.assignment.classroom.teacher == request.user
        if request.method in permissions.SAFE_METHODS:
            return is_owner or is_teacher
        if getattr(view, "action", None) == "grade":
            return is_teacher
        return is_owner
