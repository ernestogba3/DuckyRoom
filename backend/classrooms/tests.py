from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CalendarEvent, ClassRoom

User = get_user_model()


class ClassroomPermissionTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="profe", email="profe@test.com", password="ClaveSegura123", role=User.Role.TEACHER
        )
        self.student = User.objects.create_user(
            username="alumno", email="alumno@test.com", password="ClaveSegura123", role=User.Role.STUDENT
        )
        self.classroom = ClassRoom.objects.create(name="Matemáticas", teacher=self.teacher)
        self.classroom.students.add(self.student)

    def test_estudiante_no_puede_publicar_anuncios(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/announcements/", {"classroom": self.classroom.id, "content": "Hola"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_no_puede_crear_tareas(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/assignments/", {"classroom": self.classroom.id, "title": "Tarea"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profesor_si_puede_publicar_anuncios(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post(
            "/api/announcements/", {"classroom": self.classroom.id, "content": "Hola"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CalendarEventTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="profe", email="profe@test.com", password="ClaveSegura123", role=User.Role.TEACHER
        )
        self.student = User.objects.create_user(
            username="alumno", email="alumno@test.com", password="ClaveSegura123", role=User.Role.STUDENT
        )
        self.outsider = User.objects.create_user(
            username="ajeno", email="ajeno@test.com", password="ClaveSegura123", role=User.Role.STUDENT
        )
        self.classroom = ClassRoom.objects.create(name="Historia", teacher=self.teacher)
        self.classroom.students.add(self.student)

    def test_estudiante_puede_crear_un_proyecto(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/events/",
            {
                "classroom": self.classroom.id,
                "title": "Proyecto de la Revolución Francesa",
                "event_type": "PROJECT",
                "date": "2026-10-15",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"]["username"], "alumno")

    def test_alguien_de_fuera_no_puede_crear_eventos(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.post(
            "/api/events/",
            {"classroom": self.classroom.id, "title": "Examen", "event_type": "EXAM", "date": "2026-10-15"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_solo_se_ven_eventos_de_tus_clases(self):
        CalendarEvent.objects.create(
            classroom=self.classroom, created_by=self.teacher,
            title="Examen final", event_type="EXAM", date="2026-10-20",
        )
        self.client.force_authenticate(self.outsider)
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filtro_por_mes(self):
        for fecha in ["2026-10-05", "2026-11-05"]:
            CalendarEvent.objects.create(
                classroom=self.classroom, created_by=self.teacher,
                title=f"Evento {fecha}", event_type="EXAM", date=fecha,
            )
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/events/?month=2026-10")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["date"], "2026-10-05")

    def test_mes_con_formato_invalido_da_error_claro(self):
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/events/?month=octubre")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_un_estudiante_no_puede_borrar_el_evento_de_otro(self):
        evento = CalendarEvent.objects.create(
            classroom=self.classroom, created_by=self.teacher,
            title="Examen final", event_type="EXAM", date="2026-10-20",
        )
        self.client.force_authenticate(self.student)
        response = self.client.delete(f"/api/events/{evento.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_puedes_borrar_tu_propio_evento(self):
        evento = CalendarEvent.objects.create(
            classroom=self.classroom, created_by=self.student,
            title="Proyecto en grupo", event_type="PROJECT", date="2026-10-20",
        )
        self.client.force_authenticate(self.student)
        response = self.client.delete(f"/api/events/{evento.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
