import random
import string

from django.conf import settings
from django.db import models


def generate_class_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class ClassRoom(models.Model):
    name = models.CharField(max_length=120)
    section = models.CharField(max_length=60, blank=True)
    subject = models.CharField(max_length=60, blank=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=6, unique=True, default=generate_class_code)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taught_classes"
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="enrolled_classes", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Announcement(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="announcements")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Anuncio de {self.author} en {self.classroom}"


class Assignment(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.classroom.name})"


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        EXAM = "EXAM", "Examen"
        PROJECT = "PROJECT", "Proyecto"
        OTHER = "OTHER", "Otro"

    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="events")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_events"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=10, choices=EventType.choices, default=EventType.OTHER)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "created_at"]

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title} ({self.date})"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to="submissions/", null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Entrega de {self.student} para {self.assignment}"
