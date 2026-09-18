from rest_framework.routers import DefaultRouter

from .views import (
    AnnouncementViewSet,
    AssignmentViewSet,
    CalendarEventViewSet,
    ClassRoomViewSet,
    SubmissionViewSet,
)

router = DefaultRouter()
router.register("classrooms", ClassRoomViewSet, basename="classroom")
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("events", CalendarEventViewSet, basename="event")
router.register("submissions", SubmissionViewSet, basename="submission")

urlpatterns = router.urls
